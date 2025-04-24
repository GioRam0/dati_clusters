#importo librerie
import geopandas as gp
import ee
import os
import sys
import pickle

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

#importo le features dei paesi
paesi = ee.FeatureCollection('FAO/GAUL_SIMPLIFIED_500m/2015/level0')

#dizionario da riempire
countries={}
#itero per le isole
j=0
for i,isl in gdf.iterrows():
    if j%200==0:
        print(j)
    j+=1
    multi=isl.geometry
    codice=isl.ALL_Uniq
    multip_list =[ 
            [list(vertice) for vertice in poligono.exterior.coords]
            for poligono in multi.geoms
        ]   
    ee_geometry = ee.Geometry.MultiPolygon(multip_list)
    #trovo paesi intersezione
    paesi_contenenti = paesi.filterBounds(ee_geometry)
    nomi_paesi = paesi_contenenti.aggregate_array('ADM0_NAME').getInfo()
    isl.countries=nomi_paesi
    countries[codice]=nomi_paesi

#isole controllate manualmente per intersezioni non riconosciute
countries[88882]=['Maldives']
countries[89785]=['Bangladesh']
countries[89792]=['Bangladesh']
countries[89794]=['Bangladesh']
countries[89937]=['Pakistan']
countries[90195]=['China']
countries[90433]=['Republic of Korea']
countries[277103]=['Brazil']
countries[277105]=['Brazil']
countries[277239]=['Fiji']
countries[277594]=['Indonesia']
countries[277763]=['Indonesia']
countries[280098]=['Bangladesh']
countries[280538]=['Viet Nam']
countries[280549]=['Viet Nam']
countries[280552]=['Viet Nam']
countries[280664]=['China']
countries[283115]=['Solomon Islands']
countries[283862]=['Indonesia']
countries[289686]=['Viet Nam']
countries[290776]=['Norway']
countries[340640]=['China']
countries[340642]=['China']
countries[370285]=['Viet Nam']

#esportazione
percorso_folder_out = os.path.join(cartella_progetto, "data/isole_filtrate")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_file=os.path.join(percorso_folder_out, "nazioni.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(countries, f)