#importo librerie
import geopandas as gp
import ee
import pickle
import os
import sys
from shapely import Polygon

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")

#importo coordinate isole
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate/finali", "isole_arro3.gpkg")
gdf = gp.read_file(isl_path)
gdf=gdf.sort_values(by='IslandArea', ascending=False)

#percorso file config e importo la variabile project
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
import config
proj = config.proj
ee.Initialize(project=proj)

#se gia presenti (effettuata una precedente run ma interrotta) importo i dati precedentemente scaricati per non ricominciare
output_folder = os.path.join(cartella_progetto, "data/dati_finali/superficie_res")
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, "superficie_res.pkl")
if os.path.exists(output_path):
    with open(output_path, 'rb') as file:
        superficie_res = pickle.load(file)
    output_path = os.path.join(output_folder, "ele_max.pkl")
    with open(output_path ,  'rb') as file:
        ele_max = pickle.load(file)
#se non presenti inizializzo i dizionari
else:
    superficie_res={}
    ele_max={}

#dataset delle aree protette, da escludere
wdpa_polygons = ee.FeatureCollection('WCMC/WDPA/current/polygons')
#dataset sulle caratteristiche del terreno, seleziono l'immagine piu recente
lc100_collection = ee.ImageCollection("COPERNICUS/Landcover/100m/Proba-V-C3/Global")
lc_image = ee.Image(lc100_collection.sort('system:time_start', False).first())
#valori corrispondenti ai terreni non agibili per impianti rinnovabili
excluded_values = [0, 40, 50, 70, 80, 111, 112, 113, 114, 115, 116]
#dataset sull'elevazione
ele=ee.ImageCollection("JAXA/ALOS/AW3D30/V3_2")        
        
#itero per le isole
print(f"{len(gdf)} isole da svolgere")
lista=[]
for k, (i, isl) in enumerate(gdf.iterrows(), 1):
    #esportazione periodica per non dover riiniziare da capo in caso di interruzione
    if k%100==0 or k==len(gdf):
        print(f"{k} isole svolte")
        print(f"area isola: {isl.IslandArea}")
    if k % 10 == 0:
        output_path=os.path.join(output_folder, "superficie_res.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(superficie_res, f)
        output_path=os.path.join(output_folder, "ele_max.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(ele_max, f)
    codice=isl.ALL_Uniq
    if codice not in superficie_res:
        try:
            #semplifico le geometrie troppo grandi
            if isl.IslandArea>10000:
                geometria=isl.geometry.simplify(tolerance=0.005, preserve_topology=True)
            elif isl.IslandArea>5000:
                geometria=isl.geometry.simplify(tolerance=0.003, preserve_topology=True)
            elif isl.IslandArea>2000:
                geometria=isl.geometry.simplify(tolerance=0.002, preserve_topology=True)
            else:
                geometria=isl.geometry.simplify(tolerance=0.001, preserve_topology=True)
            #rendo la geometria locale una ee.Geometry e ne calcolo l'area
            if isinstance(geometria, Polygon):
                vertici_list = [vertice for vertice in geometria.exterior.coords]
                ee_geometry_original = ee.Geometry.Polygon(vertici_list)
            else:
                multip_list = [
                    [vertice for vertice in poligono.exterior.coords]
                    for poligono in geometria.geoms
                ]
                ee_geometry_original = ee.Geometry.MultiPolygon(multip_list)
            area0=ee_geometry_original.area().getInfo()

            #trovo le immagini elevazione che intersecano l'isola
            collection=ele.filterBounds(ee_geometry_original)
            #se una sola (isola interamente contenuta) creo la maschera, la applico ed estraggo le geometrie
            if collection.size().getInfo()==1:
                ele_clip=collection.first().clip(ee_geometry_original).select('DSM')
                #calcolo l'elevazione massima, se minore di 2000 non calcolo la maschera
                max_value_dict = ele_clip.reduceRegion(
                    reducer=ee.Reducer.max(),
                    geometry=ee_geometry_original,
                    scale=ele_clip.projection().nominalScale(),
                    bestEffort=True,
                    maxPixels=1e9
                ).get('DSM')
                e_max=max_value_dict.getInfo()
                ele_max[codice]=e_max
                scale = ele_clip.projection().nominalScale().getInfo()
                ee_geometry=ee_geometry_original
                if e_max>2000:
                    ele_mask=ele_clip.gt(2000)
                    vectors_ele = ele_mask.selfMask().reduceToVectors(
                        geometry=ele_mask.geometry(),
                        scale=scale,
                        crs=ele_mask.projection().crs(),
                        eightConnected=True,
                        bestEffort=True
                    )
                    #estraggo le geometrie e le sottraggo alla ee_geometry originale
                    ele_geometry=vectors_ele.union(ee.ErrorMargin(1)).geometry()
                    ee_geometry=ee_geometry.difference(ele_geometry)   
            #se piu di una immagine itero per queste ripetendo il processo
            else:
                list=collection.toList(collection.size())
                ee_geometry=ee_geometry_original
                e_max=0
                for j in range(collection.size().getInfo()):
                    img=ee.Image(list.get(j)).clip(ee_geometry_original).select('DSM')
                    max_value_dict = img.reduceRegion(
                        reducer=ee.Reducer.max(),
                        geometry=ee_geometry_original,
                        scale=img.projection().nominalScale(),
                        bestEffort=True,
                        maxPixels=1e9
                    ).get('DSM')
                    e_max1=max_value_dict.getInfo()
                    #aggiorno l'elevazione massima
                    if e_max1 is not None:
                        if e_max1>e_max:
                            e_max=e_max1
                        scale = img.projection().nominalScale().getInfo()
                        #se massimo maggiore di 2000 creo la maschera ed estraggo la geometria
                        if e_max1>2000:
                            ele_mask = img.gt(2000)
                            vectors_ele = ele_mask.selfMask().reduceToVectors(
                                geometry=ele_mask.geometry(),
                                scale=scale,
                                crs=ele_mask.projection().crs(),
                                eightConnected=True,
                                bestEffort=True
                            )
                            ele_geometry=vectors_ele.union(ee.ErrorMargin(1)).geometry()
                            ee_geometry=ee_geometry.difference(ele_geometry)
                ele_max[codice]=e_max

            #trovo le aree protetette che intersecano l'isola e levo la loro intersezione dalla geometria rimanente dell'isola
            intersecting_wdpa = wdpa_polygons.filter(ee.Filter.intersects('.geo', ee_geometry_original))
            union_of_intersecting_wdpa = intersecting_wdpa.union()
            ee_geometry = ee_geometry.difference(union_of_intersecting_wdpa)
            #se rimane trppo poco terreno (2 ettari, corrispondo a meno di un MW di fotovoltaico), mi fermo
            area=ee_geometry.area().getInfo()
            if area<20000:
                superficie_res[codice]=0
                continue

            #clippo l'immagine dei terreni sulla geometria e creo una maschera per i valori non validi
            lc_clipped = lc_image.clip(ee_geometry)
            lc_mask = lc_clipped.select('discrete_classification').eq(excluded_values[0])
            scale = lc_mask.select('discrete_classification').projection().nominalScale().getInfo()
            for val in excluded_values[1:]:
                lc_mask = lc_mask.Or(lc_clipped.select('discrete_classification').eq(val))
            vectors = lc_mask.selfMask().reduceToVectors(
                geometry=lc_mask.geometry(),
                scale=scale,
                crs=lc_mask.projection().crs(),
                eightConnected=True,
                bestEffort=True
            )
            #estraggo la geometria
            lc_geometry=vectors.union(ee.ErrorMargin(1)).geometry()
            #per isole grandi calcolo l'area della parte eliminabile e la sottraggo all'area precedente, l'approssimazione per le isole grandi è meno rilevante 
            if isl.IslandArea>2000:
                area_eliminabile=lc_geometry.area().getInfo()
                area_finale=max(area-area_eliminabile,0)
            else:
                ee_geometry=ee_geometry.difference(lc_geometry)
                area_finale=ee_geometry.area().getInfo()
            if area_finale<20000:
                superficie_res[codice]=0
                continue
            #aggiorno il dizionario
            superficie_res[codice]=(area_finale/area0)*100
        except Exception as e:
            lista.append(k)
            print(e)

#ripeto per le isole che hanno avuto exception
#sottraggo singolarmente le aree protette alla geometria dell'isola, il problema è la loro unione
print(f'Isole problematiche: {len(lista)}')
h=0
for k, (i, isl) in enumerate(gdf.iterrows(), 1):
    if k in lista:
        codice=isl.ALL_Uniq
        if codice not in superficie_res:
            print(k)
            try:
                #semplifico le geometrie troppo grandi
                if isl.IslandArea>10000:
                    geometria=isl.geometry.simplify(tolerance=0.005, preserve_topology=True)
                elif isl.IslandArea>5000:
                    geometria=isl.geometry.simplify(tolerance=0.003, preserve_topology=True)
                elif isl.IslandArea>2000:
                    geometria=isl.geometry.simplify(tolerance=0.002, preserve_topology=True)
                else:
                    geometria=isl.geometry.simplify(tolerance=0.001, preserve_topology=True)
                #rendo la geometria locale una ee.Geometry e ne calcolo l'area
                if isinstance(geometria, Polygon):
                    vertici_list = [vertice for vertice in geometria.exterior.coords]
                    ee_geometry_original = ee.Geometry.Polygon(vertici_list)
                else:
                    multip_list = [
                        [vertice for vertice in poligono.exterior.coords]
                        for poligono in geometria.geoms
                    ]
                    ee_geometry_original = ee.Geometry.MultiPolygon(multip_list)
                area0=ee_geometry_original.area().getInfo()

                #trovo le immagini elevazione che intersecano l'isola
                collection=ele.filterBounds(ee_geometry_original)
                #se una sola (isola interamente contenuta) creo la maschera, la applico ed estraggo le geometrie
                if collection.size().getInfo()==1:
                    ele_clip=collection.first().clip(ee_geometry_original).select('DSM')
                    #calcolo l'elevazione massima, se minore di 2000 non calcolo la maschera
                    max_value_dict = ele_clip.reduceRegion(
                        reducer=ee.Reducer.max(),
                        geometry=ee_geometry_original,
                        scale=ele_clip.projection().nominalScale(),
                        bestEffort=True,
                        maxPixels=1e9
                    ).get('DSM')
                    e_max=max_value_dict.getInfo()
                    ele_max[codice]=e_max
                    scale = ele_clip.projection().nominalScale().getInfo()
                    ee_geometry=ee_geometry_original
                    if e_max>2000:
                        ele_mask=ele_clip.gt(2000)
                        vectors_ele = ele_mask.selfMask().reduceToVectors(
                            geometry=ele_mask.geometry(),
                            scale=scale,
                            crs=ele_mask.projection().crs(),
                            eightConnected=True,
                            bestEffort=True
                        )
                        #estraggo le geometrie e le sottraggo alla ee_geometry originale
                        ele_geometry=vectors_ele.union(ee.ErrorMargin(1)).geometry()
                        ee_geometry=ee_geometry.difference(ele_geometry)   
                #se piu di una immagine itero per queste ripetendo il processo
                else:
                    list=collection.toList(collection.size())
                    ee_geometry=ee_geometry_original
                    e_max=0
                    for j in range(collection.size().getInfo()):
                        img=ee.Image(list.get(j)).clip(ee_geometry_original).select('DSM')
                        max_value_dict = img.reduceRegion(
                            reducer=ee.Reducer.max(),
                            geometry=ee_geometry_original,
                            scale=img.projection().nominalScale(),
                            bestEffort=True,
                            maxPixels=1e9
                        ).get('DSM')
                        e_max1=max_value_dict.getInfo()
                        #aggiorno l'elevazione massima
                        if e_max1 is not None:
                            if e_max1>e_max:
                                e_max=e_max1
                            scale = img.projection().nominalScale().getInfo()
                            #se massimo maggiore di 2000 creo la maschera ed estraggo la geometria
                            if e_max1>2000:
                                ele_mask = img.gt(2000)
                                vectors_ele = ele_mask.selfMask().reduceToVectors(
                                    geometry=ele_mask.geometry(),
                                    scale=scale,
                                    crs=ele_mask.projection().crs(),
                                    eightConnected=True,
                                    bestEffort=True
                                )
                                ele_geometry=vectors_ele.union(ee.ErrorMargin(1)).geometry()
                                ee_geometry=ee_geometry.difference(ele_geometry)
                    ele_max[codice]=e_max

                #trovo le aree protetette che intersecano l'isola e levo la loro intersezione dalla geometria rimanente dell'isola
                intersecting_wdpa = wdpa_polygons.filter(ee.Filter.intersects('.geo', ee_geometry_original))
                #creo una lista contenente le geometrie e le sottraggo iterativamente alla geometria
                feature_list = intersecting_wdpa.toList(intersecting_wdpa.size().getInfo())
                for i in range(intersecting_wdpa.size().getInfo()):
                    geometry = ee.Feature(feature_list.get(i)).geometry()
                    ee_geometry=ee_geometry.difference(ee_geometry)
                #se rimane trppo poco terreno (2 ettari, corrispondo a meno di un MW di fotovoltaico), mi fermo
                area=ee_geometry.area().getInfo()
                if area<20000:
                    superficie_res[codice]=0
                    continue

                #clippo l'immagine dei terreni sulla geometria e creo una maschera per i valori non validi
                lc_clipped = lc_image.clip(ee_geometry)
                lc_mask = lc_clipped.select('discrete_classification').eq(excluded_values[0])
                scale = lc_mask.select('discrete_classification').projection().nominalScale().getInfo()
                for val in excluded_values[1:]:
                    lc_mask = lc_mask.Or(lc_clipped.select('discrete_classification').eq(val))
                vectors = lc_mask.selfMask().reduceToVectors(
                    geometry=lc_mask.geometry(),
                    scale=scale,
                    crs=lc_mask.projection().crs(),
                    eightConnected=True,
                    bestEffort=True
                )
                #estraggo la geometria
                lc_geometry=vectors.union(ee.ErrorMargin(1)).geometry()
                #per isole grandi calcolo l'area della parte eliminabile e la sottraggo all'area precedente, l'approssimazione per le isole grandi è meno rilevante 
                if isl.IslandArea>2000:
                    area_eliminabile=lc_geometry.area().getInfo()
                    area_finale=max(area-area_eliminabile,0)
                else:
                    ee_geometry=ee_geometry.difference(lc_geometry)
                    area_finale=ee_geometry.area().getInfo()
                if area_finale<20000:
                    superficie_res[codice]=0
                    continue
                superficie_res[codice]=(area_finale/area0)*100
            
            except Exception as e:
                lista.append(k)
                print(e)
        h+=1
        print(f'{h} isole svolte')

#esportazione
percorso_folder_out = os.path.join(cartella_progetto, "data/dati_finali/superficie_res")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_file=os.path.join(percorso_folder_out, "superficie_res.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(superficie_res, f)
percorso_file=os.path.join(percorso_folder_out, "ele_max.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(ele_max, f)