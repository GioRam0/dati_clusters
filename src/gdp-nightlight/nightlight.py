#importo librerie
import numpy as np
import geopandas as gp
import ee
import pickle
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

#dataset riferimento, considero la media dei due anni piu recenti per ridurre la varianza, non ci sono dati precedenti
dataset_2022 = ee.ImageCollection("NOAA/VIIRS/DNB/ANNUAL_V22").filterDate("2022-01-01", "2022-12-31").first()
dataset_2023 = ee.ImageCollection("NOAA/VIIRS/DNB/ANNUAL_V22").filterDate("2023-01-01", "2023-12-31").first()

#ultima data disponibile
#sorted_collection = dataset_2022.sort('system:time_start',False)
#last_image = sorted_collection.first()
#timestamp_ms = last_image.get('system:time_start').getInfo()
#import datetime
#last_date = datetime.datetime.fromtimestamp(timestamp_ms/1000.0)
#print(last_date)
#print(svjs)

night_lights=ee.ImageCollection([dataset_2022, dataset_2023]).mean()

def get_median_lights(multi):
    multip_list = [
        [list(vertice) for vertice in poligono.exterior.coords]
        for poligono in multi.geoms
    ]
    multip_geo = ee.Geometry.MultiPolygon(multip_list)
    #riporta la somma nel periodo considerato all'interno della figura fornita in input
    value = night_lights.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=multip_geo,
        scale=500,  # Risoluzione in metri
        bestEffort=True
    )
    return value.get('average_masked').getInfo()

#se gia presenti (effettuata una precedente run ma interrotta) importo i dati precedentemente scaricati per non ricominciare
output_folder = os.path.join(cartella_progetto, "data/dati_finali/nightlight")
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

#itero per le isole
k=0
for i,isl in gdf.iterrows():
    if k % 200 == 0:
        #esportazione periodica per non dover riiniziare da capo in caso di interruzione
        print(k)
        output_path=os.path.join(output_folder, "nightlights.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(lights_mean, f)
        output_path=os.path.join(output_folder, "nightlights_procapite.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(lights_mean_procapite, f)
        output_path=os.path.join(output_folder, "nightlights_nodata.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(lights_mean_nodata, f)
    k+=1
    codice=isl.ALL_Uniq
    if codice not in lights_mean:
        multipoli=isl.geometry
        popolazione=isl.popolazione
        value=get_median_lights(multipoli)
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