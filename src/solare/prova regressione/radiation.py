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
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate_arro4.gpkg")
gdf = gp.read_file(isl_path)
gdf=gdf[(gdf['IslandArea']<10000)]

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo la variabile project
import config
proj = config.proj
ee.Initialize(project=proj)

#scelgo il dataset e seleziono diversi anni per ridurre la varianza
dataset=ee.ImageCollection("ECMWF/ERA5_LAND/MONTHLY_AGGR")
dataset=dataset.filterDate("2024-01-01", "2024-12-31")

#ultima data disponibile
#sorted_collection = dataset.sort('system:time_start', False)
#last_image = sorted_collection.first()
#timestamp_ms = last_image.get('system:time_start').getInfo()
#print(timestamp_ms)
#import datetime
#last_date = datetime.datetime.fromtimestamp(timestamp_ms/1000.0)
#print(last_date)

#funzioni per calcolare medie di temperatura e prcipitazioni
def mean_heat(image):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=multip_geo,
        scale=1000,  # Risoluzione MODIS
        bestEffort=True
    )
    return image.set("mean_heat", stats.get("surface_latent_heat_flux_sum"), "date", image.date().format())
def mean_rad(image):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=multip_geo,
        scale=1000,  # Risoluzione MODIS
        bestEffort=True
    )
    return image.set("mean_rad", stats.get("surface_net_solar_radiation_sum"), "date", image.date().format())
def mean_down(image):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=multip_geo,
        scale=1000,  # Risoluzione MODIS
        bestEffort=True
    )
    return image.set("mean_down", stats.get("surface_solar_radiation_downwards_sum"), "date", image.date().format())
def mean_ther(image):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=multip_geo,
        scale=1000,  # Risoluzione MODIS
        bestEffort=True
    )
    return image.set("mean_ther", stats.get("surface_net_thermal_radiation_sum"), "date", image.date().format())
def mean_trd(image):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=multip_geo,
        scale=1000,  # Risoluzione MODIS
        bestEffort=True
    )
    return image.set("mean_trd", stats.get("surface_thermal_radiation_downwards_sum"), "date", image.date().format())


#se gia presenti (effettuata una precedente run ma interrotta) importo i dati precedentemente scaricati per non ricominciare
output_folder = os.path.join(cartella_corrente)
output_path = os.path.join(output_folder, "heat.pkl")
if os.path.exists(output_path):
    with open(output_path, 'rb') as file:
        heat = pickle.load(file)
    output_path = os.path.join(cartella_corrente, "heat_nodata.pkl")
    with open(output_path ,  'rb') as file:
        heat_nodata = pickle.load(file)
    output_path = os.path.join(cartella_corrente, "rad.pkl")
    with open(output_path ,  'rb') as file:
        rad = pickle.load(file)
    output_path = os.path.join(cartella_corrente, "rad_nodata.pkl")
    with open(output_path ,  'rb') as file:
        rad_nodata = pickle.load(file)
    output_path = os.path.join(cartella_corrente, "down.pkl")
    with open(output_path ,  'rb') as file:
        down = pickle.load(file)
    output_path = os.path.join(cartella_corrente, "down_nodata.pkl")
    with open(output_path ,  'rb') as file:
        down_nodata = pickle.load(file)
    output_path = os.path.join(cartella_corrente, "ther.pkl")
    with open(output_path ,  'rb') as file:
        ther = pickle.load(file)
    output_path = os.path.join(cartella_corrente, "ther_nodata.pkl")
    with open(output_path ,  'rb') as file:
        ther_nodata = pickle.load(file)
    output_path = os.path.join(cartella_corrente, "trd.pkl")
    with open(output_path ,  'rb') as file:
        trd = pickle.load(file)
    output_path = os.path.join(cartella_corrente, "trd_nodata.pkl")
    with open(output_path ,  'rb') as file:
        trd_nodata = pickle.load(file)
#se non presenti inizializzo i dizionari
else:
    heat={}
    heat_nodata={}
    rad={}
    rad_nodata={}
    down={}
    down_nodata={}
    ther={}
    ther_nodata={}
    trd={}
    trd_nodata={}

#itero per le isole
k=0
for i,isl in gdf.iterrows():
    if k % 10 == 0:
        #esportazione periodica per non dover riiniziare da capo in caso di interruzione
        print(k)
        output_path=os.path.join(output_folder, "heat.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(heat, f)
        output_path=os.path.join(output_folder, "heat_nodata.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(heat_nodata, f)
        output_path=os.path.join(output_folder, "rad.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(rad, f)
        output_path=os.path.join(output_folder, "rad_nodata.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(rad_nodata, f)
        output_path=os.path.join(output_folder, "down.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(down, f)
        output_path=os.path.join(output_folder, "down_nodata.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(down_nodata, f)
        output_path=os.path.join(output_folder, "ther.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(ther, f)
        output_path=os.path.join(output_folder, "ther_nodata.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(ther_nodata, f)
        output_path=os.path.join(output_folder, "trd.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(trd, f)
        output_path=os.path.join(output_folder, "trd_nodata.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(trd_nodata, f)
    k+=1
    codice=isl.ALL_Uniq
    if codice not in heat:
        multipoli=isl.geometry
        multip_list = [
            [list(vertice) for vertice in poligono.exterior.coords]
            for poligono in multipoli.geoms
        ]
        multip_geo = ee.Geometry.MultiPolygon(multip_list)
        
        heat_means = dataset.map(mean_heat)
        mean_list1 = heat_means.aggregate_array("mean_heat").getInfo()
        if mean_list1==[]:
            heat[codice]=np.nan
            heat_nodata[codice]=1
        else:
            #temperatura espressa in kelvin
            heat[codice]=np.mean(mean_list1)-273
            heat_nodata[codice]=0
    
        rad_means = dataset.map(mean_rad)
        mean_list2 = rad_means.aggregate_array("mean_rad").getInfo()
        if mean_list2==[]:
            rad[codice]=np.nan
            rad_nodata[codice]=1
        else:
            #faccio la media sui quattro anni
            rad[codice]=(np.sum(mean_list2))/4
            rad_nodata[codice]=0

        down_means = dataset.map(mean_down)
        mean_list2 = down_means.aggregate_array("mean_down").getInfo()
        if mean_list2==[]:
            down[codice]=np.nan
            down_nodata[codice]=1
        else:
            #faccio la media sui quattro anni
            down[codice]=(np.sum(mean_list2))/4
            down_nodata[codice]=0

        ther_means = dataset.map(mean_ther)
        mean_list2 = ther_means.aggregate_array("mean_ther").getInfo()
        if mean_list2==[]:
            ther[codice]=np.nan
            ther_nodata[codice]=1
        else:
            #faccio la media sui quattro anni
            ther[codice]=(np.sum(mean_list2))/4
            ther_nodata[codice]=0

        trd_means = dataset.map(mean_trd)
        mean_list2 = trd_means.aggregate_array("mean_trd").getInfo()
        if mean_list2==[]:
            trd[codice]=np.nan
            trd_nodata[codice]=1
        else:
            #faccio la media sui quattro anni
            trd[codice]=(np.sum(mean_list2))/4
            trd_nodata[codice]=0

#esportazione
output_path=os.path.join(output_folder, "heat.pkl")
with open(output_path, "wb") as f:
    pickle.dump(heat, f)
output_path=os.path.join(output_folder, "heat_nodata.pkl")
with open(output_path, "wb") as f:
    pickle.dump(heat_nodata, f)
output_path=os.path.join(output_folder, "rad.pkl")
with open(output_path, "wb") as f:
    pickle.dump(rad, f)
output_path=os.path.join(output_folder, "rad_nodata.pkl")
with open(output_path, "wb") as f:
    pickle.dump(rad_nodata, f)
output_path=os.path.join(output_folder, "down.pkl")
with open(output_path, "wb") as f:
    pickle.dump(down, f)
output_path=os.path.join(output_folder, "down_nodata.pkl")
with open(output_path, "wb") as f:
    pickle.dump(down_nodata, f)
output_path=os.path.join(output_folder, "ther.pkl")
with open(output_path, "wb") as f:
    pickle.dump(ther, f)
output_path=os.path.join(output_folder, "ther_nodata.pkl")
with open(output_path, "wb") as f:
    pickle.dump(ther_nodata, f)
output_path=os.path.join(output_folder, "trd.pkl")
with open(output_path, "wb") as f:
    pickle.dump(trd, f)
output_path=os.path.join(output_folder, "trd_nodata.pkl")
with open(output_path, "wb") as f:
    pickle.dump(trd_nodata, f)