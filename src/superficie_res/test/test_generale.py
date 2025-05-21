#importo librerie
import geopandas as gp
import ee
import os
import sys
import geemap
from shapely import Polygon

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..", "..")

#importo coordinate isole
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate/finali", "isole_arro3.gpkg")
gdf = gp.read_file(isl_path)
gdf=gdf.sort_values(by='IslandArea', ascending=False)

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo la variabile project
import config
proj = config.proj
ee.Initialize(project=proj)

#folder dove esporto le mappe
output_folder = os.path.join(cartella_progetto, "data/dati_finali/superficie_res/visualizzazione")
os.makedirs(output_folder, exist_ok=True)

#dataset delle aree protette, da escludere
wdpa_polygons = ee.FeatureCollection('WCMC/WDPA/current/polygons')
#importo dataset sulle caratteristiche del terreno e seleziono l'immagine piu recente
lc100_collection = ee.ImageCollection("COPERNICUS/Landcover/100m/Proba-V-C3/Global")
lc_image = ee.Image(lc100_collection.sort('system:time_start', False).first())
#valori corrispondenti ai terreni non agibili
excluded_values = [0, 40, 50, 70, 80, 111, 112, 113, 114, 115, 116]
#dataset con immagini sull'elevazione
ele=ee.ImageCollection("JAXA/ALOS/AW3D30/V3_2")

#itero per le isole
for k, (i, isl) in enumerate(gdf.iterrows(), 1):
    if (k-1)%50==0:
        print(f'{k-1} indice')
        print(f'{isl.IslandArea} area df')
        #geometeria dell'isola, conversione in ee.geometry e layer isola originale
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
        #calcolo l'area di questa figura ed esporto la geometria come layer della mappa
        area0=ee_geometry_original.area().getInfo()
        print(f'{area0} area ee')
        m = geemap.Map()
        m.add_layer(ee_geometry_original, {'color': 'white'}, f'Isola originale')

        #aree protette che intersecano l'isola
        intersecting_wdpa = wdpa_polygons.filter(ee.Filter.intersects('.geo', ee_geometry_original))
        union_of_intersecting_wdpa = intersecting_wdpa.union()
        #elimino le aree protette
        ee_geometry_protected = ee_geometry_original.difference(union_of_intersecting_wdpa)
        #calcolo l'area e agiungo il layer alla mappa
        area1=ee_geometry_protected.area().getInfo()
        print(f'{area1} area eliminate protette')
        m.add_layer(ee_geometry_protected, {'color': 'yellow'}, f'Isola protected')

        #trovo le immagini elevazione che intersecano l'isola
        collection=ele.filterBounds(ee_geometry_original)
        #se una sola (isola interamente contenuta) creo una maschera dei punti a elevazione maggiore di 2000, ne estraggo la geometria e la sottraggo alla geometria dell'siola
        if collection.size().getInfo()==1:
            ele_clip=collection.first().clip(ee_geometry_original).select('DSM')
            ele_mask=ele_clip.gt(2000)
            scale = ele_clip.projection().nominalScale().getInfo()
            vectors_alt = ele_mask.selfMask().reduceToVectors(
                geometry=ele_mask.geometry(),
                scale=scale,
                crs=ele_mask.projection().crs(),
                eightConnected=True,
                bestEffort=True
            )
            ele_geometry=vectors_alt.union(ee.ErrorMargin(1)).geometry()
            ee_geometry_alti=ee_geometry_original.difference(ele_geometry, ee.ErrorMargin(1))
        #se piu di una immagine itero per queste ripetendo le operazioni
        else:
            list=collection.toList(collection.size())
            ee_geometry_alti=ee_geometry_original
            for j in range(collection.size().getInfo()):
                img=ee.Image(list.get(j)).clip(ee_geometry_original).select('DSM')
                mask_alt = img.gt(2000)
                scale = img.projection().nominalScale().getInfo()
                vectors_alt = mask_alt.selfMask().reduceToVectors(
                    geometry=mask_alt.geometry(),
                    scale=scale,
                    crs=mask_alt.projection().crs(),
                    eightConnected=True,
                    bestEffort=True
                )
                ele_geometry=vectors_alt.union(ee.ErrorMargin(1)).geometry()
                ee_geometry_alti=ee_geometry_alti.difference(ele_geometry, ee.ErrorMargin(1))

        #calcolo l'area rimanente e aggiungo il layer alla mappa
        area1=ee_geometry_alti.area().getInfo()
        print(f'{area1} area altitudine')
        m.add_layer(ee_geometry_alti, {'color': 'orange'}, f'Isola altitudine')
        
        #calcolo la geometria finale come intersezione delle due
        ee_geometry_final=ee_geometry_protected.intersection(ee_geometry_alti)

        #immagine copertura terreni, per le isole grandi considero solo la parte rimanente, svolgo operazioni diverse
        if isl.IslandArea>2000:
            lc_clipped=lc_image.clip(ee_geometry_final)
        else:
            lc_clipped = lc_image.clip(ee_geometry_original)
        #creo la maschera per i valori non validi, la applico, estraggo la geometria
        lc_mask = lc_clipped.select('discrete_classification').eq(excluded_values[0])
        for val in excluded_values[1:]:
            lc_mask = lc_mask.Or(lc_clipped.select('discrete_classification').eq(val))
        scale = lc_mask.select('discrete_classification').projection().nominalScale().getInfo()
        vectors = lc_mask.selfMask().reduceToVectors(
            geometry=lc_mask.geometry(),
            scale=scale,
            crs=lc_mask.projection().crs(),
            eightConnected=True,
            bestEffort=True
        )
        lc_geometry=vectors.union(ee.ErrorMargin(1)).geometry()
        #per isole grandi esporto la geometria delle parti eliminabili, ne calcolo l'area e la sottraggo all'area che rimaneva
        #operazione difference troppo dispendiosa ma approssimazione in percentuale poco rilevante
        if isl.IslandArea>2000:
            m.add_layer(lc_geometry, {'color' : 'green'}, 'Terreni eliminabili')
            area_eliminabile=lc_geometry.area().getInfo()
            area=ee_geometry_final.area().getInfo()
            area_finale=max(area-area_eliminabile, 0)
        #per le altre isole estraggo la geometria, la sottraggo, calcolo l'area e la aggiungo
        else:
            ee_geometry_terreni=ee_geometry_original.difference(lc_geometry, ee.ErrorMargin(1))
            #calcolo l'area e aggiungo il layer alla mappa
            area1=ee_geometry_terreni.area().getInfo()
            print(f'{area1} area eliminati terreni')
            m.add_layer(ee_geometry_terreni, {'color': 'green'}, f'Isola terreni agibili')
            
            #creo la geometria finale e ne calcolo l'area
            ee_geometry_final=ee_geometry_final.intersection(ee_geometry_terreni)
            area_finale=ee_geometry_final.area().getInfo()
        
        print(f'{area_finale} area finale')
        m.add_layer(ee_geometry_final, {'color': 'blue'}, f'Isola finale')
            
        #imposto la mappa e la esporto
        m.centerObject(ee_geometry_original,zoom=10)
        output_path = os.path.join(output_folder, f"mappa_interattiva{k-1}.html")
        m.to_html(output_path)