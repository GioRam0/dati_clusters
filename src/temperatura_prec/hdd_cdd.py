#importo librerie
import numpy as np
import geopandas as gp
import ee
import os
import sys
import pickle
from shapely import MultiPolygon, Polygon

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

dataset = ee.ImageCollection("ECMWF/ERA5/DAILY") \
    .filterDate("2016-06-01", "2020-05-31")
#media tutti i valori dei pixel all'interno del poligono
def mean_temp(image):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),  # media temperature
        geometry=multip_geo,
        bestEffort=True
    )
    return image.set("mean_temp", stats.get("mean_2m_air_temperature"), "date", image.date().format())

#se gia presenti (effettuata una precedente run ma interrotta) importo i dati precedentemente scaricati per non ricominciare
output_folder = os.path.join(cartella_progetto, "data/dati_finali/meteorologici")
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, "hdd.pkl")
if os.path.exists(output_path):
    with open(output_path, 'rb') as file:
        hdd = pickle.load(file)
    output_path = os.path.join(output_folder, "hdd_nodata.pkl")
    with open(output_path ,  'rb') as file:
        hdd_nodata = pickle.load(file)
    output_path = os.path.join(output_folder, "cdd.pkl")
    with open(output_path ,  'rb') as file:
        cdd = pickle.load(file)
    output_path = os.path.join(output_folder, "cdd_nodata.pkl")
    with open(output_path ,  'rb') as file:
        cdd_nodata = pickle.load(file)
#se non presenti inizializzo i dizionari
else:
     hdd={}
     hdd_nodata={}
     cdd={}
     cdd_nodata={}

gdf=gdf.sort_values(by='IslandArea', ascending=False)

#itero per le isole
k=0
for i,isl in gdf.iterrows():
    if k % 10 == 0:
        if k % 100 == 0:
            print(k)
        #esportazione periodica per non dover riiniziare da capo in caso di interruzione
        output_path=os.path.join(output_folder, "hdd.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(hdd, f)
        output_path=os.path.join(output_folder, "hdd_nodata.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(hdd_nodata, f)
        output_path=os.path.join(output_folder, "cdd.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(cdd, f)
        output_path=os.path.join(output_folder, "cdd_nodata.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(cdd_nodata, f)
    k+=1
    codice=isl.ALL_Uniq
    if codice not in hdd:
        #semplifico le geometrie troppo grandi
        if isl.IslandArea>10000:
            simpli=isl.geometry.simplify(tolerance=0.005, preserve_topology=True)
            if type(simpli) is MultiPolygon:
                multi=simpli
            if type(simpli) is Polygon:
                multi=MultiPolygon([simpli])
        elif isl.IslandArea>5000:
            simpli=isl.geometry.simplify(tolerance=0.003, preserve_topology=True)
            if type(simpli) is MultiPolygon:
                multi=simpli
            if type(simpli) is Polygon:
                multi=MultiPolygon([simpli])
        elif isl.IslandArea>2000:
            simpli=isl.geometry.simplify(tolerance=0.002, preserve_topology=True)
            if type(simpli) is MultiPolygon:
                multi=simpli
            if type(simpli) is Polygon:
                multi=MultiPolygon([simpli])
        else:
            simpli=isl.geometry.simplify(tolerance=0.001, preserve_topology=True)
            if type(simpli) is MultiPolygon:
                multi=simpli
            if type(simpli) is Polygon:
                multi=MultiPolygon([simpli])
        multip_list = [
            [list(vertice) for vertice in poligono.exterior.coords]
            for poligono in multi.geoms
        ]
        multip_geo = ee.Geometry.MultiPolygon(multip_list)
        collection=dataset.filterBounds(multip_geo)
        temp_means = collection.map(mean_temp)
        #lista con temperature medie giornaliere per il periodo considerato
        mean_list = temp_means.aggregate_array("mean_temp").getInfo()
        if mean_list==[]:
            hdd[codice]=np.nan
            hdd_nodata[codice]=1
            cdd[codice]=np.nan
            cdd_nodata[codice]=1
        else:
            k1=0
            k2=0
            for i in range(len(mean_list)):
                #288,291,294,297 in kelvin corrispondono ai valori per gli heating e i cooling days
                if mean_list[i]<288:
                    k1+=291-mean_list[i]
                if mean_list[i]>297:
                    k2+=mean_list[i]-294
            #valori su 4 anni, divido per 4
            hdd[codice]=k1/4
            hdd_nodata[codice]=0
            cdd[codice]=k2/4
            cdd_nodata[codice]=0

#esportazione finale
output_path=os.path.join(output_folder, "hdd.pkl")
with open(output_path, "wb") as f:
    pickle.dump(hdd, f)
output_path=os.path.join(output_folder, "hdd_nodata.pkl")
with open(output_path, "wb") as f:
    pickle.dump(hdd_nodata, f)
output_path=os.path.join(output_folder, "cdd.pkl")
with open(output_path, "wb") as f:
    pickle.dump(cdd, f)
output_path=os.path.join(output_folder, "cdd_nodata.pkl")
with open(output_path, "wb") as f:
    pickle.dump(cdd_nodata, f)