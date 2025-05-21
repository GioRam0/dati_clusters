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
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate/finali", "isole_arro3.gpkg")
gdf = gp.read_file(isl_path)

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo la variabile project
import config
proj = config.proj
ee.Initialize(project=proj)

output_folder = os.path.join(cartella_progetto, "data/dati_finali/urban/visualizzazione")
os.makedirs(output_folder, exist_ok=True)

#importo il dataset e seleziono l'ultima immagine presente, non futura
urban_collection=ee.ImageCollection("JRC/GHSL/P2023A/GHS_SMOD_V2-0")
filtered_collection=urban_collection.filterDate('2000-01-01', '2025-01-01')
sorted_collection=filtered_collection.sort('system:time_start', False)
urban_image=ee.Image(sorted_collection.first())
#valori dei pixel urbani
urban_values = [30, 23, 22]

gdf=gdf.sort_values(by='IslandArea', ascending=False)
#itero per le isole
for k, (i, isl) in enumerate(gdf.iterrows(), 1):
    if k%100==0:
        print(f'isola {k}')
        #geometeria dell'isola e conversione in ee.geometry
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
        #creo la mappa e aggiungo il layer dell'isola originale
        m = geemap.Map()
        m.add_layer(ee_geometry_original, {'color': 'green'}, f'Isola originale')
        m.centerObject(ee_geometry_original,zoom=10)
        #clipp dell'immagine urbana e creazione di una maschera con valori associati alle aree urbane
        clipped_image = urban_image.clip(ee_geometry_original)
        urban_mask = clipped_image.eq(urban_values[0])
        urban_mask = urban_mask.Or(clipped_image.eq(urban_values[1]))
        urban_mask = urban_mask.Or(clipped_image.eq(urban_values[2]))
        #estrazione delle geometrie dalla maschera e aggiunta del layer alla mappa
        vectors = urban_mask.selfMask().reduceToVectors(
            geometry=urban_mask.geometry(),
            scale=clipped_image.projection().nominalScale().getInfo(),
            eightConnected=True,
            bestEffort=True
        )
        urban_geometry = vectors.union(ee.ErrorMargin(1)).geometry()
        urban_geometry = urban_geometry.intersection(ee_geometry_original)
        m.add_layer(urban_geometry, {'color': 'blue'}, f'Isola urban')
        #esporto la mappa
        m.centerObject(ee_geometry_original,zoom=10)
        output_path = os.path.join(output_folder, f"mappa_interattiva{k}.html")
        m.to_html(output_path)