#importo librerie
import numpy as np
import geopandas as gp
import ee
import pickle
import os
import sys

#vedi i dataset
# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..", "..")

#importo coordinate isole
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate_arro4.gpkg")
gdf = gp.read_file(isl_path)
gdf=gdf[(gdf['IslandArea'])<100000]

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo la variabile project
import config
proj = config.proj
ee.Initialize(project=proj)

#scelgo il dataset e seleziono diversi anni per ridurre la varianza
dataset=ee.ImageCollection("MODIS/061/MOD21C3")
dataset=dataset.filterDate("2022-01-01", "2024-12-31")

#ultima data disponibile
#sorted_collection = dataset.sort('system:time_start', False)
#last_image = sorted_collection.first()
#timestamp_ms = last_image.get('system:time_start').getInfo()
#print(timestamp_ms)
#import datetime
#last_date = datetime.datetime.fromtimestamp(timestamp_ms/1000.0)
#print(last_date)

#funzioni per calcolare medie di temperatura e prcipitazioni
def mean_temp2(image):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=multip_geo,
        scale=1000,  # Risoluzione MODIS
        bestEffort=True
    )
    return image.set("mean_temp2", stats.get("LST_AVE"), "date", image.date().format())


#se gia presenti (effettuata una precedente run ma interrotta) importo i dati precedentemente scaricati per non ricominciare
output_folder = os.path.join(cartella_corrente)
output_path = os.path.join(output_folder, "temp2.pkl")
if os.path.exists(output_path):
    with open(output_path, 'rb') as file:
        temp2 = pickle.load(file)
    output_path = os.path.join(cartella_corrente, "temp2_nodata.pkl")
    with open(output_path ,  'rb') as file:
        temp2_nodata = pickle.load(file)

#se non presenti inizializzo i dizionari
else:
    temp2={}
    temp2_nodata={}

#itero per le isole
k=0
for i,isl in gdf.iterrows():
    if k % 50 == 0:
        #esportazione periodica per non dover riiniziare da capo in caso di interruzione
        print(k)
        output_path=os.path.join(output_folder, "temp2.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(temp2, f)
        output_path=os.path.join(output_folder, "temp2_nodata.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(temp2_nodata, f)
    k+=1
    codice=isl.ALL_Uniq
    if codice not in temp2:
        multipoli=isl.geometry
        multip_list = [
            [list(vertice) for vertice in poligono.exterior.coords]
            for poligono in multipoli.geoms
        ]
        multip_geo = ee.Geometry.MultiPolygon(multip_list)
        collection=dataset.filterBounds(multip_geo)
        temp2_means = collection.map(mean_temp2)
        mean_list1 = temp2_means.aggregate_array("mean_temp2").getInfo()
        if mean_list1==[]:
            temp2[codice]=np.nan
            temp2_nodata[codice]=1
        else:
            #temperatura espressa in kelvin
            temp2[codice]=np.mean(mean_list1)-273
            temp2_nodata[codice]=0

#esportazione
output_path=os.path.join(output_folder, "temp2.pkl")
with open(output_path, "wb") as f:
    pickle.dump(temp2, f)
output_path=os.path.join(output_folder, "temp2_nodata.pkl")
with open(output_path, "wb") as f:
    pickle.dump(temp2_nodata, f)