#importo librerie
import numpy as np
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
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2_arro4.gpkg")
gdf = gp.read_file(isl_path)

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo la variabile project
import config
proj = config.proj
ee.Initialize(project=proj)

#dataset riferimento, considero la media dei due anni piu recenti per ridurre la varianza, non ci sono dati precedenti
collection = ee.ImageCollection("NOAA/VIIRS/DNB/ANNUAL_V22")

#vedendo le date di inizio delle foto e il numero di immagini nella collezione si capisce che ci sono tre immagini relative a 2022,2023 e 2024
sorted_collection = collection.sort('system:time_start',False)
last_image = sorted_collection.first()
timestamp_ms = last_image.get('system:time_start').getInfo()
import datetime
last_date = datetime.datetime.fromtimestamp(timestamp_ms/1000.0)
print(last_date)

sorted_collection = collection.sort('system:time_start')
first_image = sorted_collection.first()
timestamp_ms = first_image.get('system:time_start').getInfo()
import datetime
first_date = datetime.datetime.fromtimestamp(timestamp_ms/1000.0)
print(first_date)

print(collection.size().getInfo())

#creo una image come media pesata dal numero di osservazioni dei tre anni
lista_images=collection.toList(collection.size().getInfo())
multi1=(ee.Image(lista_images.get(0)).select('average_masked')).multiply(ee.Image(lista_images.get(0)).select('cf_cvg'))
multi2=(ee.Image(lista_images.get(1)).select('average_masked')).multiply(ee.Image(lista_images.get(1)).select('cf_cvg'))
multi3=(ee.Image(lista_images.get(2)).select('average_masked')).multiply(ee.Image(lista_images.get(2)).select('cf_cvg'))
numeratore=multi1.add(multi2).add(multi3)
denominatore=(ee.Image(lista_images.get(0)).select('cf_cvg')).add(ee.Image(lista_images.get(1)).select('cf_cvg')).add(ee.Image(lista_images.get(2)).select('cf_cvg'))
mean=numeratore.divide(denominatore).rename('viirs_weighted_mean')
scale=mean.projection().nominalScale().getInfo()

def get_median_lights(geom):
    #riporta la somma nel periodo considerato all'interno della figura fornita in input
    value = mean.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=geom,
        scale=scale,
        bestEffort=True
    )
    return value.get('viirs_weighted_mean').getInfo()

#se gia presenti (effettuata una precedente run ma interrotta) importo i dati precedentemente scaricati per non ricominciare
output_folder = os.path.join(cartella_progetto, "data/dati_finali/gdp_nightlight")
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, "nightlights.pkl")
if os.path.exists(output_path):
    with open(output_path, 'rb') as file:
        lights_mean = pickle.load(file)
    output_path = os.path.join(output_folder, "nightlights_procapite.pkl")
    with open(output_path , 'rb') as file:
        lights_mean_procapite = pickle.load(file)
    output_path = os.path.join(output_folder, "nightlights_nodata.pkl")
    with open(output_path ,  'rb') as file:
        lights_mean_nodata = pickle.load(file)
#se non presenti inizializzo i dizionari
else:
    lights_mean={}
    lights_mean_procapite={}
    lights_mean_nodata={}

gdf=gdf.sort_values(by='IslandArea', ascending=True)
#itero per le isole
for k, (i, isl) in enumerate(gdf.iterrows(), 1):
    if k % 1 == 0:
        #esportazione periodica per non dover riiniziare da capo in caso di interruzione
        print(k)
        print(isl.IslandArea)
        output_path=os.path.join(output_folder, "nightlights.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(lights_mean, f)
        output_path=os.path.join(output_folder, "nightlights_procapite.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(lights_mean_procapite, f)
        output_path=os.path.join(output_folder, "nightlights_nodata.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(lights_mean_nodata, f)
    codice=isl.ALL_Uniq
    if codice not in lights_mean:
        #creo le ee.geometry, con isole grandi le semplifico per non superare il payload massimo
        if isl.IslandArea>30000:
            geometria=isl.geometry.simplify(tolerance=0.005, preserve_topology=True)
            if isinstance(geometria, Polygon):
                vertici_list = [vertice for vertice in geometria.exterior.coords]
                ee_geometry = ee.Geometry.Polygon(vertici_list)
            else:
                multip_list = [
                    [vertice for vertice in poligono.exterior.coords]
                    for poligono in geometria.geoms
                ]
                ee_geometry = ee.Geometry.MultiPolygon(multip_list)
        else:
            geometria=isl.geometry
            multip_list = [
                [vertice for vertice in poligono.exterior.coords]
                for poligono in geometria.geoms
            ]
            ee_geometry = ee.Geometry.MultiPolygon(multip_list)
        popolazione=isl.Popolazione
        value=get_median_lights(ee_geometry)
        if ((value==None) | (value==None)):
            lights_mean[codice]=np.nan
            lights_mean_nodata[codice]=1
            lights_mean_procapite[codice]=np.nan
        else:
            lights_mean[codice]=value
            lights_mean_nodata[codice]=0
            lights_mean_procapite[codice]=value/popolazione

#esportazione
output_path=os.path.join(output_folder, "nightlights.pkl")
with open(output_path, "wb") as f:
    pickle.dump(lights_mean, f)
output_path=os.path.join(output_folder, "nightlights_procapite.pkl")
with open(output_path, "wb") as f:
    pickle.dump(lights_mean_procapite, f)
output_path=os.path.join(output_folder, "nightlights_nodata.pkl")
with open(output_path, "wb") as f:
    pickle.dump(lights_mean_nodata, f)