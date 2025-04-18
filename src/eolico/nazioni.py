#importo librerie
import geopandas as gp
import ee
import os
import sys

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")

#importo coordinate isole
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2_arro2.gpkg")
gdf = gp.read_file(isl_path)

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo la variabile project
import config
proj = config.proj
ee.Initialize(project=proj)

#importo le features dei paesi
paesi = ee.FeatureCollection('FAO/GAUL_SIMPLIFIED_500m/2015/level0')

#creo una colonna con liste vuote da riempire nel dataframe
gdf["countries"] = [[] for _ in range(len(gdf))]
#itero per le isole
k=0
for i,isl in gdf.iterrows():
    multi=isl.geometry
    multip_list =[ 
            [list(vertice) for vertice in poligono.exterior.coords]
            for poligono in multi.geoms
        ]   
    ee_geometry = ee.Geometry.MultiPolygon(multip_list)
    #trovo paesi intersezione
    paesi_contenenti = paesi.filterBounds(ee_geometry)
    nomi_paesi = paesi_contenenti.aggregate_array('ADM0_NAME').getInfo()
    isl.countries=nomi_paesi
    gdf.loc[i,'countries']=nomi_paesi
    
#esportazione gpkg
#percorso_out = os.path.join(cartella_progetto, "data/isole_filtrate/isole_filtrate_nazioni.gpkg")
#gdf.to_file(percorso_out, driver="GPKG")