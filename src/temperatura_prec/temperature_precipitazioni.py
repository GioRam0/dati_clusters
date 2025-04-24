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
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2_arro4.gpkg")
gdf = gp.read_file(isl_path)

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo la variabile project
import config
proj = config.proj
ee.Initialize(project=proj)

#scelgo il dataset e seleziono diversi anni per ridurre la varianza
dataset = ee.ImageCollection("ECMWF/ERA5/MONTHLY")
dataset=dataset.filterDate("2016-06-01", "2020-05-31")

#ultima data disponibile
#sorted_collection = dataset.sort('system:time_start', False)
#last_image = sorted_collection.first()
#timestamp_ms = last_image.get('system:time_start').getInfo()
#print(timestamp_ms)
#import datetime
#last_date = datetime.datetime.fromtimestamp(timestamp_ms/1000.0)
#print(last_date)

#funzioni per calcolare medie di temperatura e prcipitazioni
def mean_temp(image):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),  # media temperature
        geometry=multip_geo,
        scale=1000,  # Risoluzione MODIS
        bestEffort=True
    )
    return image.set("mean_temp", stats.get("mean_2m_air_temperature"), "date", image.date().format())
def mean_prec(image):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),  # media precipitazioni
        geometry=multip_geo,
        bestEffort=True
    )
    return image.set("mean_prec", stats.get("total_precipitation"), "date", image.date().format())

#se gia presenti (effettuata una precedente run ma interrotta) importo i dati precedentemente scaricati per non ricominciare
output_folder = os.path.join(cartella_progetto, "data/dati_finali/meteorologici")
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, "temp.pkl")
if os.path.exists(output_path):
    with open(output_path, 'rb') as file:
            temp = pickle.load(file)
    output_path = os.path.join(cartella_corrente, "temp_nodata.pkl")
    with open(output_path ,  'rb') as file:
            temp_nodata = pickle.load(file)
    output_path = os.path.join(cartella_corrente, "prec.pkl")
    with open(output_path ,  'rb') as file:
            prec = pickle.load(file)
    output_path = os.path.join(cartella_corrente, "prec_nodata.pkl")
    with open(output_path ,  'rb') as file:
            prec_nodata = pickle.load(file)
#se non presenti inizializzo i dizionari
else:
    temp={}
    temp_nodata={}
    prec={}
    prec_nodata={}

#itero per le isole
k=0
for i,isl in gdf.iterrows():
    if k % 200 == 0:
        #esportazione periodica per non dover riiniziare da capo in caso di interruzione
        print(k)
        output_path=os.path.join(output_folder, "temp.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(temp, f)
        output_path=os.path.join(output_folder, "temp_nodata.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(temp_nodata, f)
        output_path=os.path.join(output_folder, "prec.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(prec, f)
        output_path=os.path.join(output_folder, "prec_nodata.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(prec_nodata, f)
    k+=1
    codice=isl.ALL_Uniq
    if codice not in temp:
        multipoli=isl.geometry
        multip_list = [
            [list(vertice) for vertice in poligono.exterior.coords]
            for poligono in multipoli.geoms
        ]
        multip_geo = ee.Geometry.MultiPolygon(multip_list)
        collection=dataset.filetrBounds(multip_geo)
        temp_means = collection.map(mean_temp)
        mean_list1 = temp_means.aggregate_array("mean_temp").getInfo()
        if mean_list1==[]:
            temp[codice]=np.nan
            isl_nodt[codice]=1
        else:
            #temperatura espressa in kelvin
            temp[codice]=np.mean(mean_list1)-273
            isl_nodt[codice]=0
    
        prec_means = dataset.map(mean_prec)
        mean_list2 = prec_means.aggregate_array("mean_prec").getInfo()
        if mean_list2==[]:
            prec[codice]=np.nan
            isl_nodp[codice]=1
        else:
            #faccio la media sui quattro anni
            prec[codice]=(np.sum(mean_list2))/4
            isl_nodp[codice]=0

#esportazione
percorso_folder_out = os.path.join(cartella_progetto, "data/dati_finali/meteorologici")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_file=os.path.join(percorso_folder_out, "temp.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(temp, f)
percorso_file=os.path.join(percorso_folder_out, "temp_nodata.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(isl_nodt, f)
percorso_file=os.path.join(percorso_folder_out, "annual_precipitation.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(prec, f)
percorso_file=os.path.join(percorso_folder_out, "prec_nodata.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(isl_nodp, f)