#importo librerie
import geopandas as gp
import ee
import os
import sys
import geemap
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

output_folder = os.path.join(cartella_progetto, "data/dati_finali/superficie_res/visualizzazione1")
os.makedirs(output_folder, exist_ok=True)
gdf=gdf.sort_values(by='IslandArea', ascending=True)
lista=[2503,2572,2640]
m = geemap.Map()
for k, (i, isl) in enumerate(gdf.iterrows(), 1):
    if k in lista:
        geometria=isl.geometry.simplify(tolerance=0.005, preserve_topology=True)
        if isinstance(geometria, Polygon):
            vertici_list = [vertice for vertice in geometria.exterior.coords]
            ee_geometry_original = ee.Geometry.Polygon(vertici_list)
        else:
            multip_list = [
                [vertice for vertice in poligono.exterior.coords]
                for poligono in geometria.geoms
            ]
            ee_geometry_original = ee.Geometry.MultiPolygon(multip_list)
        print(ee_geometry_original.getInfo())
        m.add_layer(ee_geometry_original, {'color': 'green'}, f'Isola originale{k}')
        m.centerObject(ee_geometry_original,zoom=10)
        output_path = os.path.join(output_folder, f"mappa_interattiva{k}.html")
        m.to_html(output_path)