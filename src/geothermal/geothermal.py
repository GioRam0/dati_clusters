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
percorso_file = os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2_arro2.gpkg")
dfisl = gp.read_file(percorso_file)

#lista ALL_Uniq di isole troppo vicine ai bordi 180, -180. applicando il buffer in coordinate utm e riconvertendo in 4326 il poligono diventerebbe una striscia. applico un buffer direttamente in 4326
lista=[292365,282309,277208, 274415, 282454,274143,344028,277249,274142,347209,347210,344026]
#funzione che prende in input un poli/multipoli e restituisce la figura con buffer
def buffer(figura,a):
    lon, lat = figura.centroid.x, figura.centroid.y
    #individuo la zona utm per usare il sistema di coordinate appropriato, necessario per i calcoli di aree
    utm_zone = utm.from_latlon(lat, lon)
    utm_crs = f"EPSG:{32600 + utm_zone[2]}"
    gf = gp.GeoDataFrame(geometry=[figura], crs="EPSG:4326")
    if a:
        gf.geometry = gf.geometry.buffer(0.18)
    else:
        gf = gf.to_crs(utm_crs)
        gf.geometry = gf.geometry.buffer(20000)
        gf = gf.to_crs('EPSG:4326')
    return gf.iloc[0]['geometry']

#dizionario con codici come chiavi e somma potenziali geotermici come valori
geotherm={}
#dizionario che assegna al nome di un sito geotermico l'isola cui è stato associato
geotherm1={}
k=0
for index_isl, isola in dfisl.iterrows(): #itero isole
    if k%100==0:
        print(k)
    k+=1
    geotherm[isola.ALL_Uniq]=0
    for index_geo, punto_geo in dfgeo.iterrows(): #itero i punti geotermici
        punto=punto_geo.geometry
        name=punto_geo.name
        #se l'isola contiene il punto aggiungo la potenza all'isola ed elimino il punto, non può essere condiviso con altre isole
        if isola.geometry.contains(punto):
            #la potenza del sito si trova in una colonna denominata q ed è una stringa con la virgola come separatore decimale
            #sostituisco la virgola con un punto e trasformo la stringa in un float
            a=float(punto_df.q.replace(",", "."))
            geotherm[isola.ALL_Uniq]+=a
            dfgeo=dfgeo.drop(index_geo)
        #se l'isola buffer contiene il punto aggiungo la potenza solo se non è assegnato ad altre isole o se questa isola è più vicina al punto della precedente
        allargato=buffer(isola.geometry)
        elif allargato.contains(punto):
            a=float(punto_df.q.replace(",", "."))
            if name not in geotherm1:
                geotherm[isola.ALL_Uniq]+=a
                geotherm1[name]=index_isl
            else:
                distanza1 = isola.geometry.distance(punto)
                isola2 = gdf.loc[geotherm1[name]]
                distanza2 = isola2.geometry.distance(punto)
                if distanza1<distanza2:
                    geotherm[isola.ALL_Uniq]+=a
                    geotherm[isola2.ALL_Uniq]-=a
                    geotherm1[name]=index_isl

#esportazione
percorso_folder_out = os.path.join(cartella_progetto, "data/dati_finali/geotermico")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_file=os.path.join(percorso_folder_out, "geothermal_potential.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(geotherm, f)