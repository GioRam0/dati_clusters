#importo le librerie
import geopandas as gp
import os
from rtree import index

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")

#importo le isole
percorso_isl = os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2.gpkg")
gdfisl = gp.read_file(percorso_isl)

#importo siti idroelettrici
percorso_hydro = os.path.join(cartella_progetto, "files", "hydro.gpkg")
gdfh = gp.read_file(percorso_hydro)

#indice per facilitare le ricerca dei punti contenuti
idx = index.Index()
for i, row in gdfh.iterrows():
    bbox = row.geometry.bounds
    idx.insert(i, bbox)

#dizionario che associa ai codici delle isola la somma delle potenze dei siti che contengono
hydro={}
#itero per le isole
k=0
for i, isola in gdfisl.iterrows():
    if k%100==0:
        print(k)
    k+=1
    codice=isola.ALL_Uniq
    poligono = isola.geometry
    bbox_isola = poligono.bounds
    #siti potenzialmente candidati, contenuti nei bounds
    candidati = list(idx.intersection(bbox_isola))
    somma_potenza = 0.0
    #controllo che i candidati siano effettivamente contenuti nell'isola
    for cand in candidati:
        punto = gdfh.loc[cand].geometry
        if poligono.contains(punto):
            somma_potenza += gdfh.loc[cand,'kWh_year_1']
    hydro[codice] = somma_potenza

#esportazione
percorso_folder_out = os.path.join(cartella_progetto, "data/dati_finali/hydro")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_file=os.path.join(percorso_folder_out, "hydro.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(hydro, f)