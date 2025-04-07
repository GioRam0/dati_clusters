#importo librerie
import numpy as np
import geopandas as gp
import ee
import pickle
import os
import sys

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..". "..")

#importo coordinate isole
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2_arro2.gpkg")
gdf = gp.read_file(isl_path)

#credenziali di accesso a API google Earth
# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo le variabili config
import config
proj = config.proj
credentials_path = os.path.join(cartella_corrente, "..", "credentials")
ee.Initialize(project='proj')

#dataset riferimento, considero la media dei due anni piu recenti per ridurre la varianza, non ci sono dati precedenti
dataset_2022 = ee.ImageCollection("NOAA/VIIRS/DNB/ANNUAL_V22").filterDate("2022-01-01", "2022-12-31").first()
dataset_2023 = ee.ImageCollection("NOAA/VIIRS/DNB/ANNUAL_V22").filterDate("2023-01-01", "2023-12-31").first()

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

#dizionario da riempire con i codici isole come chiavi e i gdp delle isole come valori
lights_mean={}
#dizionario da riempire con i codici isole come chiavi e i gdp procapite delle isole come valori
lights_mean_procapite={}
#dizionario con i codici delle isole come chiavi e un binario: 1 se l'isola non ha dati 0 se sono disponibili
isola_out={}
k=0
for ind,isl in gdf.iterrows(): #itero per le isole
    if k % 50 == 0:
        print(k)
    k+=1
    codice=isl.ALL_Uniq
    multipoli=isl.geometry
    popolazione=isl.popolazione
    value=get_median_lights(multipoli)
    if ((value==None) | (value==None)):
        lights_mean[codice]=np.nan
        isola_out[codice]=1
        lights_mean_procapite[codice]=np.nan
    else:
        lights_mean[codice]=value
        isola_out[codice]=0
        lights_mean_procapite[codice]=value/popolazione

#esportazione
percorso_folder_out = os.path.join(cartella_progetto, "data/dati_finali/gdp_nightlight")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_file=os.path.join(percorso_folder_out, "nightlights.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(lights_mean, f)
percorso_file=os.path.join(percorso_folder_out, "nightlights_procapite.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(lights_mean_procapite, f)
percorso_file=os.path.join(percorso_folder_out, "nightlights_nodata.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(isola_out, f)