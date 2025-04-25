#importo le libreria
from shapely.geometry import box, mapping
import numpy as np
import geopandas as gp
import pickle
import os

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")

#importo isole e file siti geotermici
percorso_file = os.path.join(cartella_progetto, "files", "geothermal_potential.gpkg")
dfgeo = gp.read_file(percorso_file)
percorso_file = os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2.gpkg")
dfisl = gp.read_file(percorso_file)
percorso_file = os.path.join(cartella_progetto, "data/isole_filtrate", "isole_buffer.gpkg")
dfbuf = gp.read_file(percorso_file)

#aggiungere colonna geom buf

#dizionario con codici come chiavi e somma potenziali geotermici come valori
geotherm={elemento: 0 for elemento in list(dfisl.ALL_Uniq)}
#dizionario che assegna al nome di un sito geotermico l'isola cui è stato associato
geotherm1={}

k=0
#itero per le isole
for index_isl, isola in dfisl.iterrows():
    if k%100==0:
        print(k)
    k+=1
    multi=isola.geometry
    codice=isola.ALL_Uniq
    buffer=dfbuf[dfbuf['ALL_Uniq'] == codice].iloc[0]['geometry']
    for index_geo, punto_geo in dfgeo.iterrows(): #itero i punti geotermici
        punto=punto_geo.geometry
        #se l'isola contiene il punto aggiungo la potenza all'isola ed elimino il punto, non può essere condiviso con altre isole
        if multi.contains(punto):
            #la potenza del sito si trova in una colonna denominata q ed è una stringa con la virgola come separatore decimale
            #sostituisco la virgola con un punto e trasformo la stringa in un float
            a=float(punto_geo.q.replace(",", "."))
            geotherm[codice]+=a
            dfgeo=dfgeo.drop(index_geo)
        
        if buffer.contains(punto):
            a=float(punto_geo.q.replace(",", "."))
            #se il sito non è stato associato a nessuna isola li associo
            if index_geo not in geotherm1:
                geotherm[codice]+=a
                geotherm1[index_geo]=index_isl
            #altrimenti controllo qualle delle due isole è più vicina
            else:
                distanza1 = isola.geometry.distance(punto)
                isola2 = dfisl.loc[geotherm1[index_geo]]
                distanza2 = isola2.geometry.distance(punto)
                if distanza1<distanza2:
                    geotherm[codice]+=a
                    geotherm[isola2.ALL_Uniq]-=a
                    geotherm1[index_geo]=index_isl

#esportazione
percorso_folder_out = os.path.join(cartella_progetto, "data/dati_finali/geotermico")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_file=os.path.join(percorso_folder_out, "geothermal_potential.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(geotherm, f)#