#importo librerie
import geopandas as gp
import numpy as np
import ee
import pickle
import os
import sys
from shapely import Polygon

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")

#importo coordinate isole
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2_arro3.gpkg")
gdf = gp.read_file(isl_path)

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo la variabile project
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
    output_path = os.path.join(output_folder, "superficie_nodata.pkl")
    with open(output_path , 'rb') as file:
        superficie_nodata = pickle.load(file)
    output_path = os.path.join(output_folder, "ele_max.pkl")
    with open(output_path ,  'rb') as file:
        ele_max = pickle.load(file)
#se non presenti inizializzo i dizionari
else:
    superficie_res={}
    superficie_nodata={}
    ele_max={}
#2572,2640 isolata posso fare rettangolo
lista=[2683,2572,2640,2503,2494,2468,2440,2757,2768, 2780,2817,2829]
gdf=gdf.sort_values(by='IslandArea', ascending=True)
#itero per le isole
for k, (i, isl) in enumerate(gdf.iterrows(), 1):
    if k % 1 == 0 and k>2810:
        #esportazione periodica per non dover riiniziare da capo in caso di interruzione
        if k%1==0:
            print(k)
            print(isl.IslandArea)
        output_path=os.path.join(output_folder, "superficie_res.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(superficie_res, f)
        output_path=os.path.join(output_folder, "superficie_nodata.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(superficie_nodata, f)
        output_path=os.path.join(output_folder, "ele_max.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(ele_max, f)
    codice=isl.ALL_Uniq
    if codice not in superficie_res and k not in lista:
        #semplifico le geometrie troppo grandi
        if isl.IslandArea>10000:
            geometria=isl.geometry.simplify(tolerance=0.005, preserve_topology=True)
        elif isl.IslandArea>5000:
            geometria=isl.geometry.simplify(tolerance=0.003, preserve_topology=True)
        elif isl.IslandArea>2000:
            geometria=isl.geometry.simplify(tolerance=0.002, preserve_topology=True)
        else:
            geometria=isl.geometry.simplify(tolerance=0.001, preserve_topology=True)
        if isinstance(geometria, Polygon):
            vertici_list = [vertice for vertice in geometria.exterior.coords]
            ee_geometry = ee.Geometry.Polygon(vertici_list)
        else:
            multip_list = [
                [vertice for vertice in poligono.exterior.coords]
                for poligono in geometria.geoms
            ]
            ee_geometry = ee.Geometry.MultiPolygon(multip_list)

        #calcolo l'area di questa figura
        area0=ee_geometry.area().getInfo()

        #dataset delle aree protette, da escludere
        wdpa_polygons = ee.FeatureCollection('WCMC/WDPA/current/polygons')
        #aree che intersecano l'isola
        intersecting_wdpa = wdpa_polygons.filter(ee.Filter.intersects('.geo', ee_geometry))
        #elimino le aree protette
        union_of_intersecting_wdpa = intersecting_wdpa.union()
        ee_geometry = ee_geometry.difference(union_of_intersecting_wdpa)
        #se rimane trppo poco terreno (2 ettari, corrispondo a meno di un MW di fotovoltaico)
        #mi fermo
        if ee_geometry.area().getInfo()<20000:
            superficie_res[codice]=0
            superficie_nodata[codice]=0
            continue
        ##importo image sull'elevazione
        #ele=ee.Image("USGS/GMTED2010_FULL")
        ##ritaglio sull'isola e seleziono la banda opportuna
        #ele_clip=ele.clip(ee_geometry)
        ##creo una maschera con i pixel con elevazione <2000 metri, applico la maschera e ricavo la nuova geometria
        #ele_mask=ele_clip.slect('mea').lt(2000)
        #scale = ele_clip.select('mea').projection().nominalScale().getInfo()
        #vectors = ele_mask.selfMask().reduceToVectors(
        #    geometry=ele_mask.geometry(),
        #    scale=scale,
        #    crs=ele_mask.projection().crs(),
        #    eightConnected=True,
        #    bestEffort=True
        #)
        ##unisco le geometrie e le interseco alla geometria precedente
        #ele_geometry=vectors.union(ee.ErrorMargin(1)).geometry()
        #ee_geometry=ee_geometry.intersection(ele_geometry, ee.ErrorMargin(1))
        ##calcolo elevazione max
        #max_value_dict = ele_clip.reduceRegion(
        #    reducer=ee.Reducer.max(),
        #    geometry=ee_geometry,
        #    scale=scale,
        #    bestEffort=True,
        #    maxPixels=1e9
        #).get('max')
        #max=max_value_dict.getInfo()
        #ele_max[codice]=max
        #
        ##calcolo l'image con la pendenza e creo la maschera con i valori minori di 11.31 gradi (20%)
        #slope = ee.Terrain.slope(ele_clip)
        #slope_mask=slope.select('slope').lt(11.31)
        #vectors = slope_mask.selfMask().reduceToVectors(
        #    geometry=slope_mask.geometry(),
        #    scale=scale,
        #    crs=slope_mask.projection().crs(),
        #    eightConnected=True,
        #    bestEffort=True
        #)
        #slope_geometry=vectors.union(ee.ErrorMargin(1)).geometry()
        #ee_geometry=ee_geometry.intersection(slope_geometry, ee.ErrorMargin(1))
    
        #importo il dataset sull'elevazione
        ele=ee.ImageCollection("JAXA/ALOS/AW3D30/V3_2")
        #trovo le immagini che intersecano l'isola
        collection=ele.filterBounds(ee_geometry)
        #se una sola (isola interamente contenuta) creo la maschera e la applico
        if collection.size().getInfo()==1:
            #clippo l'immagine elevazione sulla geometria, genero una maschera con i valori minori di 2000 e ne estraggo le geometrie
            ele_clip=collection.first().clip(ee_geometry)
            ele_mask=ele_clip.select('DSM').lt(2000)
            scale = ele_clip.select('DSM').projection().nominalScale().getInfo()
            vectors = ele_mask.selfMask().reduceToVectors(
                geometry=ele_mask.geometry(),
                scale=scale,
                crs=ele_mask.projection().crs(),
                eightConnected=True,
                bestEffort=True
            )
            #unisco queste geometrie e le interseco con le ee_geometry
            ele_geometry=vectors.union(ee.ErrorMargin(1)).geometry()
            ee_geometry=ee_geometry.intersection(ele_geometry, ee.ErrorMargin(1))
            #calcolo anche l'elevazione massima
            max_value_dict = ele_clip.reduceRegion(
                reducer=ee.Reducer.max(),
                geometry=ee_geometry,
                scale=ele_clip.select('DSM').projection().nominalScale(),
                bestEffort=True,
                maxPixels=1e9
            ).get('DSM')
            max=max_value_dict.getInfo()
            ele_max[codice]=max
            #stesso processo con la slope<11.31 (gradi, corrisponde al 20%)
            slope = ee.Terrain.slope(ele_clip)
            slope_mask=slope.select('slope').lt(11.31)
            scale = ele_clip.select('DSM').projection().nominalScale().getInfo()
            vectors = slope_mask.selfMask().reduceToVectors(
                geometry=slope_mask.geometry(),
                scale=scale,
                crs=ele_clip.select('DSM').projection().crs(),
                eightConnected=True,
                bestEffort=True
            )
            slope_geometry=vectors.union(ee.ErrorMargin(1)).geometry()
            ee_geometry=ee_geometry.intersection(slope_geometry, ee.ErrorMargin(1))
        #se piu di uno itero per le diverse immagini e calcolo le zone da escludere sottraedole di volta in volta dalla ee_geometry, processo simile ma inverso
        else:
            list=collection.toList(collection.size())
            max=0
            for j in range(collection.size().getInfo()):
                img=ee.Image(list.get(j)).clip(ee_geometry)
                mask = img.select('DSM').gt(2000)
                scale = img.select('DSM').projection().nominalScale().getInfo()
                vectors = mask.selfMask().reduceToVectors(
                    geometry=mask.geometry(),
                    scale=scale,
                    crs=mask.projection().crs(),
                    eightConnected=True,
                    bestEffort=True
                )
                ele_geometry=vectors.union(ee.ErrorMargin(1)).geometry()
                ee_geometry=ee_geometry.difference(ele_geometry, ee.ErrorMargin(1))
                
                max_value_dict = img.reduceRegion(
                    reducer=ee.Reducer.max(),
                    geometry=ee_geometry,
                    scale=img.select('DSM').projection().nominalScale(),
                    bestEffort=True,
                    maxPixels=1e9
                ).get('DSM')
                max1=max_value_dict.getInfo()
                if max1 is not None:
                    if max1>max:
                        max=max1
                
                slope = ee.Terrain.slope(img)
                slope_mask=slope.select('slope').lt(11.31)
                scale = img.select('DSM').projection().nominalScale().getInfo()
                vectors = slope_mask.selfMask().reduceToVectors(
                    geometry=slope_mask.geometry(),
                    scale=scale,
                    crs=img.select('DSM').projection().crs(),
                    eightConnected=True,
                    bestEffort=True
                )
                slope_geometry=vectors.union(ee.ErrorMargin(1)).geometry()
                ee_geometry=ee_geometry.difference(slope_geometry, ee.ErrorMargin(1)) 
            ele_max[codice]=max

        if ee_geometry.area().getInfo()<20000:
            superficie_res[codice]=0
            superficie_nodata[codice]=0
            continue
        #importo dataset sulle caratteristiche del terreno e seleziono l'immagine piu recente
        lc100_collection = ee.ImageCollection("COPERNICUS/Landcover/100m/Proba-V-C3/Global")
        lc_image = ee.Image(lc100_collection.sort('system:time_start', False).first())
        #valori corrispondenti ai terreni non agibili
        excluded_values = [0, 40, 50, 70, 80, 90, 111, 112, 113, 114, 115, 116, 200]
        #clippo l'immagine sulla geometria
        lc_clipped = lc_image.clip(ee_geometry)
        #maschera per i punti senza dati, se troppi raccolgo questa informazione nel dizionario nodata
        lc_mask = lc_clipped.select('discrete_classification').neq(excluded_values[0])
        scale = lc_mask.select('discrete_classification').projection().nominalScale().getInfo()
        #conto pixel validi e non validi, histogriam riporta la frequenza dei diversi valori come dizionario
        histogram = lc_mask.reduceRegion(
            reducer=ee.Reducer.frequencyHistogram(),
            geometry=ee_geometry,
            scale=scale
        ).getInfo()       
        counts = histogram['discrete_classification']
        #conto gli zeri e gli uno, se gli zeri sono piu della meta degli 1 non considero l'isola valida
        zero_count=counts.get('0',0)
        one_count=counts.get('1',0)
        if zero_count>0.5*one_count:
            superficie_nodata[codice]=1
            superficie_res[codice]=np.nan
            continue
        else:
            superficie_nodata[codice]=0
        
        #itero per gli altri terreni non agibili e applico la maschera
        for j in range(1, len(excluded_values)):
            lc_mask=lc_mask.And(lc_clipped.select('discrete_classification').neq(excluded_values[j]))

        vectors = lc_mask.selfMask().reduceToVectors(
            geometry=lc_mask.geometry(),
            scale=scale,
            crs=lc_mask.projection().crs(),
            eightConnected=True,
            bestEffort=True
        )
        lc_geometry=vectors.union(ee.ErrorMargin(1)).geometry()
        ee_geometry=ee_geometry.intersection(lc_geometry, ee.ErrorMargin(1))
    
        #area agibile
        area=ee_geometry.area().getInfo()
        superficie_res[codice]=(area/area0)*100

#esportazione
percorso_folder_out = os.path.join(cartella_progetto, "data/dati_finali/superficie_res")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_file=os.path.join(percorso_folder_out, "superficie_res.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(superficie_res, f)
percorso_file=os.path.join(percorso_folder_out, "superficie_nodata.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(superficie_nodata, f)
percorso_file=os.path.join(percorso_folder_out, "ele_max.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(ele_max, f)