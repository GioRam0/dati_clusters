#importo librerie
import geopandas as gp
import ee
import os
import sys
import numpy as np
from shapely import Polygon

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..", "..")

#importo coordinate isole
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate/finali", "isole_arro3.gpkg")
gdf = gp.read_file(isl_path)
gdf=gdf.sort_values(by='IslandArea', ascending=True)

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo la variabile project
import config
proj = config.proj
ee.Initialize(project=proj)

#importo il dataset delle coperture dei terreni e seleziono l'immagine piu recente
lc100_collection = ee.ImageCollection("COPERNICUS/Landcover/100m/Proba-V-C3/Global")
lc_image = ee.Image(lc100_collection.sort('system:time_start', False).first())
#valori corrispondenti ai terreni non agibili
excluded_values = [0, 40, 50, 70, 80, 111, 112, 113, 114, 115, 116]

#nuova colonne del dataframe
gdf['terreni']=0

#itero per le isole
for k, (i, isl) in enumerate(gdf.iterrows(), 1):
    if (k-1)%10==0:
        print(f'{k-1} indice')
        print(f'{isl.IslandArea} area df')
        #geometeria dell'isola, conversione in ee.geometry e calcolo dell'area
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
            ee_geometry_original = ee.Geometry.Polygon(vertici_list)
        else:
            multip_list = [
                [vertice for vertice in poligono.exterior.coords]
                for poligono in geometria.geoms
            ]
            ee_geometry_original = ee.Geometry.MultiPolygon(multip_list)
        area0=ee_geometry_original.area().getInfo()
        
        lc_clipped = lc_image.clip(ee_geometry_original)
        #creo la maschera per i valori non validi, la applico ed estraggo la geometria
        lc_mask=lc_clipped.select('discrete_classification').eq(excluded_values[0])
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
        ee_geometry_terr_agibili=ee_geometry_original.difference(lc_geometry, ee.ErrorMargin(1))
        #calcolo l'area e aggiorno il dataframe
        area1=ee_geometry_terr_agibili.area().getInfo()
        gdf.loc[i,'terreni']=area1/area0
    else:
        gdf=gdf.drop(i)

print(np.mean(gdf[f'terreni']))