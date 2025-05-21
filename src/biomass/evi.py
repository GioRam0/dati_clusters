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
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate/finali", "isole_arro4.gpkg")
gdf = gp.read_file(isl_path)

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo la variabile project
import config
proj = config.proj
ee.Initialize(project=proj)

#seleziono il dataset e filtro su due anni
dataset = ee.ImageCollection("MODIS/061/MOD13A3")
#ultima data disponibile
sorted_collection = dataset.sort('system:time_start', False)
last_image = sorted_collection.first()
timestamp_ms = last_image.get('system:time_start').getInfo()
import datetime
last_date = datetime.datetime.fromtimestamp(timestamp_ms/1000.0)
print(f"data dell'ultima immagine: {last_date}")
#seleziono due anni per ridurre variazioni o anomalie di un singolo anno
dataset=dataset.filterDate("2022-01-01", "2024-12-31")

#funzione che somma tutti i valori dei pixel all'interno del poligono
def mean_evi(image):
    stats = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=multip_geo,
        bestEffort=True
    )
    return image.set("mean_evi", stats.get("EVI"), "date", image.date().format())

#se gia presenti (effettuata una precedente run ma interrotta) importo i dati precedentemente scaricati per non ricominciare
output_folder = os.path.join(cartella_progetto, "data/dati_finali/biomassa")
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, "evi.pkl")
if os.path.exists(output_path):
    with open(output_path, 'rb') as file:
        evi = pickle.load(file)
    output_path = os.path.join(output_folder, "evi_nodata.pkl")
    with open(output_path ,  'rb') as file:
        evi_nodata = pickle.load(file)
#se non presenti inizializzo i dizionari
else:
    evi={}
    evi_nodata={}

print(f'isole da svolgere: {len(gdf)}')
#itero per le isole
for k, (i, isl) in enumerate(gdf.iterrows(), 1):
    if k%100 ==0 or k==len(gdf):
        print(f'{k} isole svolte')
    if k % 10 == 0:
        #esportazione periodica per non dover riiniziare da capo in caso di interruzione
        output_path=os.path.join(output_folder, "evi.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(evi, f)
        output_path=os.path.join(output_folder, "evi_nodata.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(evi_nodata, f)
    codice=isl.ALL_Uniq
    if codice not in evi:
        #semplifico le geometrie troppo grandi, eccessivo payload
        if isl.IslandArea>15000:
            simpli=isl.geometry.simplify(tolerance=0.005, preserve_topology=True)
            if isinstance(simpli, MultiPolygon):
                multi=simpli
            if isinstance(simpli, Polygon):
                multi=MultiPolygon([simpli])
        else:
            multipoli=isl.geometry
        multip_list = [
            [list(vertice) for vertice in poligono.exterior.coords]
            for poligono in multipoli.geoms
        ]
        multip_geo = ee.Geometry.MultiPolygon(multip_list)
        #clippo la collection per la figura in questione per risparmiare calcoli
        collection=dataset.filterBounds(multip_geo)
        evi_means = dataset.map(mean_evi)
        #otteniamo una lista perche il dataset ha frequenza mensile e rporta un valore per ogni mese
        evi_list = evi_means.aggregate_array("mean_evi").getInfo()
        if evi_list==[]:
            evi[codice]=np.nan
            evi_nodata[codice]=1
        else:
            #calcolo la media sui vari mesi
            evi[codice]=np.mean(evi_list)
            evi_nodata[codice]=0

#esportazione
output_path=os.path.join(output_folder, "evi.pkl")
with open(output_path, "wb") as f:
    pickle.dump(evi, f)
output_path=os.path.join(output_folder, "evi_nodata.pkl")
with open(output_path, "wb") as f:
    pickle.dump(evi_nodata, f)