#importo libreria e isole
import geopandas as gp
import os
import pickle

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..". "..")

#importo coordinate isole
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2_arro2.gpkg")
gdf = gp.read_file(isl_path)
#cartella con dati meteorologici
cartella_meteo = os.path.join(cartella_progetto, "data/dati_finali/meteorologici")
 #liste da riempire
hd=[]
hd_nod=[]
cd=[]
cd_nod=[]
#funzione che legge i file text e li trasforma in una lista
def leggi_file_come_lista(nome_file):
    with open(nome_file, 'r') as file:
        lista = [float(linea.strip()) for linea in file]
    return lista

for c in range(1,17):
    file_path=os.path.join(cartella_meteo, "hd", f"hd{c}")
    hd+=leggi_file_come_lista(file_path)
    file_path=os.path.join(cartella_meteo, "hd_nod", f"hd_nod{c}")
    hd_nod+=leggi_file_come_lista(file_path)
    file_path=os.path.join(cartella_meteo, "cd", f"cd{c}")
    cd+=leggi_file_come_lista(file_path)
    file_path=os.path.join(cartella_meteo, "cd", f"cd_nod{c}")
    cd_nod+=leggi_file_come_lista(file_path)

#traduco le liste in dizionari
hd1={}
hd_nod1={}
cd1={}
cd_nod1={}
for i in range(len(gdf)):
    codice=gdf.loc[i,'ALL_Uniq']
    hd1[codice]=hd[i]
    hd_nod1[codice]=hd_nod[i]
    cd1[codice]=cd[i]
    cd_nod1[codice]=cd_nod1[i]

#esportazione
file_path=os.path.join(cartella_meteo, "heating_days.pkl")
with open(file_path, "wb") as f:
    pickle.dump(hd1, f)
file_path=os.path.join(cartella_meteo, "hdd_nodata.pkl")
with open(file_path, "wb") as f:
    pickle.dump(hd_nod1, f)
file_path=os.path.join(cartella_meteo, "cooling_days.pkl")
with open(file_path, "wb") as f:
    pickle.dump(cd1, f)
file_path=os.path.join(cartella_meteo, "cdd_nodata.pkl")
with open(file_path, "wb") as f:
    pickle.dump(cd_nod1, f)