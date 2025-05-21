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

#dataset delle aree protette, da escludere
wdpa_polygons = ee.FeatureCollection('WCMC/WDPA/current/polygons')
#nuova colonna del dataframe
gdf['area_protected']=0

#itero per le isole
for k, (i, isl) in enumerate(gdf.iterrows(), 1):
    if (k-1)%10==0:
        print(f'{k-1} indice')
        print(f'{isl.IslandArea} area df')
        #geometeria dell'isola, conversione in ee.geometry e calcolo area
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

        #aree che intersecano l'isola
        intersecting_wdpa = wdpa_polygons.filter(ee.Filter.intersects('.geo', ee_geometry_original))
        union_of_intersecting_wdpa = intersecting_wdpa.union()
        #elimino le aree protette
        ee_geometry_protected = ee_geometry_original.difference(union_of_intersecting_wdpa)
        #calcolo l'area e aggiorno il dataframe
        area1=ee_geometry_protected.area().getInfo()
        gdf.loc[i,'area_protected']=area1/area0
    else:
        gdf=gdf.drop(i)

print(np.mean(gdf['area_protected']))