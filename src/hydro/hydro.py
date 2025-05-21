#importo le librerie
import geopandas as gp
import os
from rtree import index
import pickle

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")

#importo le isole
percorso_isl = os.path.join(cartella_progetto, "data/isole_filtrate/finali", "isole.gpkg")
gdfisl = gp.read_file(percorso_isl)

#importo siti idroelettrici
percorso_hydro = os.path.join(cartella_progetto, "files", "hydro.gpkg")
gdfh = gp.read_file(percorso_hydro)

#indice per facilitare le ricerca dei punti contenuti
print(f'punti idro da analizzare: {len(gdfh)}')
idx = index.Index()
for k,(i, row) in enumerate(gdfh.iterrows(),1):
    if k%100000==0 or k==len(gdfh):
        print(f'{k} punti idro analizzati')
    bbox = row.geometry.bounds
    idx.insert(i, bbox)

#dizionario che associa ai codici delle isola la somma delle potenze dei siti che contengono
hydro={}
#itero per le isole
print(f'isole da analizzare: {len(gdfisl)}')
for k,(i, isola) in enumerate(gdfisl.iterrows(),1):
    if k%100==0 or k==len(gdfisl):
        print(f'{k} isole analizzate')
    codice=isola.ALL_Uniq
    poligono = isola.geometry
    bbox_isola = poligono.bounds
    #siti potenzialmente candidati, contenuti nei bounds
    candidati = list(idx.intersection(bbox_isola))
    somma_potenza = 0.0
    #controllo che i candidati siano effettivamente contenuti nell'isola, in caso sommo la loro potenza a quella associata all'isola
    for cand in candidati:
        punto = gdfh.loc[cand].geometry
        if poligono.contains(punto):
            somma_potenza += gdfh.loc[cand,'kWh_year_1']
            #se associato all'isola lo elimino per facilitare le iterazioni successive
            idx.delete(cand, punto.bounds)
    #aggiorno il dizionario
    hydro[codice] = somma_potenza

#esportazione
percorso_folder_out = os.path.join(cartella_progetto, "data/dati_finali/hydro")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_file=os.path.join(percorso_folder_out, "hydro.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(hydro, f)