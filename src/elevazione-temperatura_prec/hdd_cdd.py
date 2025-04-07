#importo librerie
import numpy as np
import geopandas as gp
import ee
import os
import sys

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..". "..")

#importo coordinate isole
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2_arro2.gpkg")
gdf = gp.read_file(isl_path)
multipolygons = gdf.geometry

#credenziali di accesso a API google Earth
# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo le variabili config
import config
proj = config.proj
credentials_path = os.path.join(cartella_corrente, "..", "credentials")
ee.Initialize(project='proj')

dataset = ee.ImageCollection("ECMWF/ERA5/DAILY") \
    .filterDate("2016-06-01", "2020-05-31")
#media tutti i valori dei pixel all'interno del poligono
def mean_temp(image):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),  # media temperature
        geometry=multip_geo,
        scale=1000,  # Risoluzione MODIS
        bestEffort=True
    )
    return image.set("mean_temp", stats.get("mean_2m_air_temperature"), "date", image.date().format())

#ripeto il processo a pezzi ed esporto i dati per evitare che un'interruzione mi costringa a ricominciare da zero, riparto da dove ho interrotto
#nel caso in cui il processo si interrompa si puo far ripartire aggiornando i valori iniziali di a,b,c
a=0
b=150
c=1
hd=[]
hd_nod=[]
cd=[]
cd_nod=[]
while b<2442: #valore inserito perche nel file completo il dataframe delle isole filtrate ne contiene 2441, valore da aggiornare per la cartella light
    if b==2400:
        b=2441
    for i in range(a,b):
        if i % 50 == 0:
            print(i)
        multip_list = [
            [list(vertice) for vertice in poligono.exterior.coords]
            for poligono in multipolygons[i].geoms
        ]
        multip_geo = ee.Geometry.MultiPolygon(multip_list)
        temp_means = dataset.map(mean_temp)
        #lista con temperature medie giornaliere per il periodo considerato
        mean_list = temp_means.aggregate_array("mean_temp").getInfo()
        if mean_list==[]:
            hd.append(np.nan)
            hd_nod.append(1)
            cd.append(np.nan)
            cd_nod.append(1)
        else:
            k=0
            k1=0
            for i in range(len(mean_list)):
                #291 kelvin corrisponde a 18 celsius, valore per gli heating days
                if mean_list[i]<288:
                    k+=291-mean_list[i]
                if mean_list[i]>297:
                    k1+=mean_list[i]-294
            #valori su 4 anni, divido per 4
            hd.append(k/4)
            hd_nod.append(0)
            cd.append(k1/4)
            cd_nod.append(0)
    #esportazione delle singole librerie
    percorso_folder_mete = os.path.join(cartella_progetto, "data/dati_finali/meteorologici")
    percorso_folder_out = os.path.join(percorso_folder_mete, "hd")
    os.makedirs(percorso_folder_out, exist_ok=True)
    percorso_file = os.path.join(percorso_folder_out, f"hd{c}")
    with open(percorso_file, "w") as file_txt:
        for elemento in hd:
            file_txt.write(str(elemento) + "\n")
    percorso_folder_out = os.path.join(percorso_folder_mete, "hd_nod")
    os.makedirs(percorso_folder_out, exist_ok=True)
    percorso_file = os.path.join(percorso_folder_out, f"hd_nod{c}")
    with open(percorso_file, "w") as file_txt:
        for elemento in hd_nod:
            file_txt.write(str(elemento) + "\n")
    percorso_folder_out = os.path.join(percorso_folder_mete, "cd")
    os.makedirs(percorso_folder_out, exist_ok=True)
    percorso_file = os.path.join(percorso_folder_out, f"cd{c}")
    with open(percorso_file, "w") as file_txt:
        for elemento in cd:
            file_txt.write(str(elemento) + "\n")
    percorso_folder_out = os.path.join(percorso_folder_mete, "cd_nod")
    os.makedirs(percorso_folder_out, exist_ok=True)
    percorso_file = os.path.join(percorso_folder_out, f"cd_nod{c}")
    with open(percorso_file, "w") as file_txt:
        for elemento in cd_nod:
            file_txt.write(str(elemento) + "\n")
    a+=150
    b+=150
    c+=1