#importo librerie
import numpy as np
import geopandas as gp
import ee
import pickle
import os
import sys
from shapely import MultiPolygon, Polygon

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
dataset=ee.ImageCollection("ECMWF/ERA5_LAND/DAILY_AGGR")
dataset=dataset.select(['u_component_of_wind_10m','v_component_of_wind_10m'])
dataset1=ee.ImageCollection("ECMWF/ERA5/DAILY")
dataset1=dataset1.select(['u_component_of_wind_10m','v_component_of_wind_10m'])

#ultima data disponibile
#sorted_collection = dataset1.sort('system:time_start', False)
#last_image = sorted_collection.first()
#timestamp_ms = last_image.get('system:time_start').getInfo()
#import datetime
#last_date = datetime.datetime.fromtimestamp(timestamp_ms/1000.0)
#print(last_date)

dataset=dataset.filterDate("2016-07-01", "2020-06-30")
dataset1=dataset1.filterDate("2016-07-01", "2020-06-30")

#funzione per aggiungere una banda con cubo della velocita del vento, proporzionale alla sua potenza
#nel caso in cui viene troppo lungo faccio prima la media sul poligono e poi la elevo alla 
def wind_power(image):
    u = image.select('u_component_of_wind_10m')
    v = image.select('v_component_of_wind_10m')
    wind_speed = u.pow(2).add(v.pow(2)).sqrt()
    wind_power = wind_speed.pow(3).rename('wind_power')
    return image.addBands(wind_power)
#funzione per calcolare la potenza media
def mean_power(image):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),  # media potenze
        geometry=multip_geo,
        bestEffort=True
    )
    return image.set("mean_power", stats.get("wind_power"), "date", image.date().format())
#funzione per calcolare la deviazione standard delle potenza media mensile
def dev_std(collection):
    power_list=[]
    for i in range(1,13):
        #seleziono solo le immagini di un mese e calcolo la potenza media
        collection_month=collection.filter(ee.Filter.calendarRange(i, i, 'month'))
        #calcolo la media del wind_power tra i vari pixel e li listo
        power_means_month=collection_month.map(mean_power)
        mean_list = power_means_month.aggregate_array("mean_power").getInfo()
        power_list.append(np.mean(mean_list))
    #calcolo la devizione standard delle potenze medie mensili
    deviazione_standard=np.std(power_list)
    return deviazione_standard

#se gia presenti (effettuata una precedente run ma interrotta) importo i dati precedentemente scaricati per non ricominciare
output_folder = os.path.join(cartella_progetto, "data/dati_finali/eolico")
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, "eolico.pkl")
if os.path.exists(output_path):
    with open(output_path, 'rb') as file:
        eolico = pickle.load(file)
    output_path = os.path.join(output_folder, "eolico_nodata.pkl")
    with open(output_path , 'rb') as file:
        eolico_nodata = pickle.load(file)
    output_path = os.path.join(output_folder, "eolico_std.pkl")
    with open(output_path ,  'rb') as file:
        std = pickle.load(file)
#se non presenti inizializzo i dizionari
else:
    eolico={}
    eolico_nodata={}
    std={}

gdf=gdf.sort_values(by='IslandArea', ascending=False)

#itero per le isole
for k, (i, isl) in enumerate(gdf.iterrows(), 1):
    if k % 10 == 0:
        if k%100==0:
            print(k)
        #esportazione periodica per non dover riiniziare da capo in caso di interruzione
        output_path=os.path.join(output_folder, "eolico.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(eolico, f)
        output_path=os.path.join(output_folder, "eolico_nodata.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(eolico_nodata, f)
        output_path=os.path.join(output_folder, "eolico_std.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(std, f)
    codice=isl.ALL_Uniq
    if codice not in eolico:
        #semplifico le geometrie troppo grandi
        if isl.IslandArea>10000:
            simpli=isl.geometry.simplify(tolerance=0.005, preserve_topology=True)
        elif isl.IslandArea>5000:
            simpli=isl.geometry.simplify(tolerance=0.003, preserve_topology=True)
        elif isl.IslandArea>2000:
            simpli=isl.geometry.simplify(tolerance=0.002, preserve_topology=True)
        else:
            simpli=isl.geometry.simplify(tolerance=0.001, preserve_topology=True)
        if isinstance(simpli, MultiPolygon):
            multi=simpli
        if isinstance(simpli, Polygon):
            multi=MultiPolygon([simpli])
        multip_list = [
            [list(vertice) for vertice in poligono.exterior.coords]
            for poligono in multi.geoms
        ]
        multip_geo = ee.Geometry.MultiPolygon(multip_list)
        #clippo le immagini per il poligono e aggiungo banda wind_power
        collection=dataset.filterBounds(multip_geo)
        power_collection=collection.map(wind_power)
        #calcolo la media del wind_power tra i vari pixel e li listo
        power_means=power_collection.map(mean_power)
        mean_list = power_means.aggregate_array("mean_power").getInfo()
        if len(mean_list)>0:
            eolico[codice]=np.mean(mean_list)
            eolico_nodata[codice]=0
            std[codice]=dev_std(power_collection)
        #se l'isola non è coperta in era5-land provo con era5
        else:
            #clippo le immagini per il poligono e aggiungo banda wind_power
            collection=dataset1.filterBounds(multip_geo)
            power_collection=collection.map(wind_power)
            #calcolo la media del wind_power tra i vari pixel e li listo
            power_means=power_collection.map(mean_power)
            mean_list = power_means.aggregate_array("mean_power").getInfo()
            if len(mean_list)>0:
                eolico[codice]=np.mean(mean_list)
                eolico_nodata[codice]=0
                std[codice]=dev_std(power_means)
            #non ho modo di trovare i dati
            else:
                eolico[codice]=np.nan
                eolico_nodata[codice]=1
                std[codice]=np.nan

#esportazione
output_path=os.path.join(output_folder, "eolico.pkl")
with open(output_path, "wb") as f:
    pickle.dump(eolico, f)
output_path=os.path.join(output_folder, "eolico_nodata.pkl")
with open(output_path, "wb") as f:
    pickle.dump(eolico_nodata, f)
output_path=os.path.join(output_folder, "eolico_std.pkl")
with open(output_path, "wb") as f:
    pickle.dump(std, f)