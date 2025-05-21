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
gdf=gdf.sort_values(by='IslandArea', ascending=False)

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo la variabile project
import config
proj = config.proj
ee.Initialize(project=proj)

#dataset con immagini sull'elevazione
ele=ee.ImageCollection("JAXA/ALOS/AW3D30/V3_2")
#nuova colonna dataframe per valutare i risultati ottenuti
gdf['area_alt']=0

#itero per le isole
for k, (i, isl) in enumerate(gdf.iterrows(), 1):
    if (k-1)%10==0:
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
        #calcolo l'area di questa figura
        area0=ee_geometry_original.area().getInfo()

        #trovo le immagini che intersecano l'isola
        collection=ele.filterBounds(ee_geometry_original)
        #se una sola (isola interamente contenuta) creo la maschera ed estraggo la geometria
        if collection.size().getInfo()==1:
            ele_clip=collection.first().clip(ee_geometry_original)
            ele_mask=ele_clip.select('DSM').gt(2000)
            scale = ele_clip.select('DSM').projection().nominalScale().getInfo()
            vectors_alt = ele_mask.selfMask().reduceToVectors(
                geometry=ele_mask.geometry(),
                scale=scale,
                crs=ele_mask.projection().crs(),
                eightConnected=True,
                bestEffort=True
            )
            ele_geometry=vectors_alt.union(ee.ErrorMargin(1)).geometry()
            ee_geometry_alt=ee_geometry_original.difference(ele_geometry, ee.ErrorMargin(1))
        #se piu di una ripeto iterativamente
        else:
            list=collection.toList(collection.size())
            for j in range(collection.size().getInfo()):
                img=ee.Image(list.get(j)).clip(ee_geometry_original)
                mask_alt = img.select('DSM').gt(2000)
                scale = img.select('DSM').projection().nominalScale().getInfo()
                vectors_alt = mask_alt.selfMask().reduceToVectors(
                    geometry=mask_alt.geometry(),
                    scale=scale,
                    crs=mask_alt.projection().crs(),
                    eightConnected=True,
                    bestEffort=True
                )
                ele_geometry=vectors_alt.union(ee.ErrorMargin(1)).geometry()
                if j==0:
                    ee_geometry_alt=ee_geometry_original.difference(ele_geometry, ee.ErrorMargin(1))
                else:
                    ee_geometry_alt=ee_geometry_alt.difference(ele_geometry, ee.ErrorMargin(1))
        #calcolo l'area e aggiorno il dataframe
        area1=ee_geometry_alt.area().getInfo()
        if area1<area0:
            print(k-1)
        gdf.loc[i,'area_alt']=area1/area0
    else:
        gdf=gdf.drop(i)

print(np.mean(gdf['area_alt']))