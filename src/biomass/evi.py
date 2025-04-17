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

#credenziali di accesso a API google Earth
# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo le variabili config
import config
proj = config.proj
credentials_path = os.path.join(cartella_corrente, "..", "credentials")
ee.Initialize(project=proj)

dataset = ee.ImageCollection("MODIS/061/MOD13A3") \
    .filterDate("2022-01-01", "2023-12-31")
#funzioen che somma tutti i valori dei pixel all'interno del poligono
def mean_evi(image):
    stats = image.reduceRegion(
        reducer=ee.Reducer.sum(),  # Somma i valori EVI
        geometry=multip_geo,
        scale=1000,  # Risoluzione MODIS
        bestEffort=True
    )
    return image.set("mean_evi", stats.get("EVI"), "date", image.date().format())

#dizionario da riempire con i codici isole come chiavi e gli evi delle isole come valori
evi={}
#dizionario con i codici delle isole come chiavi e un binario: 1 se l'isola non ha dati 0 se sono disponibili
isl_nod={}
k=0
for ind,isl in gdf.iterrows(): #itero per le isole
    if k % 50 == 0:
        print(k)
    k+=1
    codice=isl.ALL_Uniq
    multipoli=isl.geometry
    multip_list = [
        [list(vertice) for vertice in poligono.exterior.coords]
        for poligono in multipoli.geoms
    ]
    multip_geo = ee.Geometry.MultiPolygon(multip_list)
    evi_means = dataset.map(mean_evi)
    #otteniamo una lista perche il dataset ha frequenza mensile e rporta un valore per ogni mese
    mean_list = evi_means.aggregate_array("mean_evi").getInfo()
    if mean_list==[]:
        evi[codice]=np.nan
        isl_nod[codice]=1
    else:
        evi[codice]=np.mean(mean_list)
        isl_nod[codice]=0

#esportazione
percorso_folder_out = os.path.join(cartella_progetto, "data/dati_finali/biomass")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_file=os.path.join(percorso_folder_out, "evi.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(evi, f)
percorso_file=os.path.join(percorso_folder_out, "evi_nodata.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(isl_nod, f)