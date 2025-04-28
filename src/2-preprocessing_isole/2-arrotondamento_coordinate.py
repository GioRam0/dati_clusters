#importo le librerie
import geopandas as gp
import os
from shapely.geometry import MultiPolygon, Polygon
from collections import OrderedDict

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")

# percorso completo per il file .gpkg
percorso_file = os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate.gpkg")
gdf = gp.read_file(percorso_file)

#funzione che arrotonda a due cifre decimali le coordinate dei vari punti
def arrotonda(poligono, cifra):
    vertici_arrotondati=[(round(x, cifra), round(y, cifra)) for x, y in poligono.exterior.coords]
    return(Polygon(vertici_arrotondati))
#funzione che elimina elementi duplicati dalla lista dei vertici di un poligono
#se in questo modo rimangono solo due punti restituisce 0 poichè non si può costruire un poligono con due vertici
def rimuovi(poligono):
    #trasforma la sequenza di vertici del poligono in un dizionario dove i vertici sono le chiavi e poi li trasforma in una lista
    #in questo processo vengono eliminati i duplicati
    vertici_uniti=list(OrderedDict.fromkeys(poligono.exterior.coords))
    if (len(vertici_uniti)>2):
        return Polygon(vertici_uniti)
    else:
        return 0
#funzione che unisce le due precedenti
def poligono_semplificato(poligono, cifra):
    poligono_arrotondato=arrotonda(poligono, cifra)
    poligonosemplificato=rimuovi(poligono_arrotondato)
#    return poligonosemplificato
print('lunghezza del file:')
print(len(gdf))
k=0
#itero per le isole
for i,isl in gdf.iterrows():
    if k%500==0:
        print(k)
    k+=1
    multi_originale=isl.geometry
    poligoni=[]
    #itero per i poligoni che compongono il multipoligono e li aggiungo alla lista
    for h in range(len(multi_originale.geoms)):
        poligono=poligono_semplificato(multi_originale.geoms[h], 4)
        if poligono!=0:
            poligoni.append(poligono)
    #imposto la geometria dell'isola come il multipoligono creato dalla lista di poligoni appena generata
    gdf.loc[i,'geometry']=MultiPolygon(poligoni)
#esportazione gpkg
percorso_out = os.path.join(cartella_progetto, "data/isole_filtrate/isole_filtrate_arro4.gpkg")
gdf.to_file(percorso_out, driver="GPKG")

k=0
#itero per le isole, ripeto con 2 e 3 cifre
for i,isl in gdf.iterrows():
    if k%500==0:
        print(k)
    k+=1
    multi_originale=isl.geometry
    poligoni=[]
    #itero per i poligoni che compongono il multipoligono e li aggiungo alla lista
    for h in range(len(multi_originale.geoms)):
        poligono=poligono_semplificato(multi_originale.geoms[h], 3)
        if poligono!=0:
            poligoni.append(poligono)
    #imposto la geometria dell'isola come il multipoligono creato dalla lista di poligoni appena generata
    gdf.loc[i,'geometry']=MultiPolygon(poligoni)
#esportazione gpkg
percorso_out = os.path.join(cartella_progetto, "data/isole_filtrate/isole_filtrate_arro3.gpkg")
gdf.to_file(percorso_out, driver="GPKG")

k=0
#itero per le isole
for i,isl in gdf.iterrows():
    if k%500==0:
        print(k)
    k+=1
    multi_originale=isl.geometry
    poligoni=[]
    #itero per i poligoni che compongono il multipoligono e li aggiungo alla lista
    for h in range(len(multi_originale.geoms)):
        poligono=poligono_semplificato(multi_originale.geoms[h], 2)
        if poligono!=0:
            poligoni.append(poligono)
    #imposto la geometria dell'isola come il multipoligono creato dalla lista di poligoni appena generata
    gdf.loc[i,'geometry']=MultiPolygon(poligoni)
#esportazione gpkg
percorso_out = os.path.join(cartella_progetto, "data/isole_filtrate/isole_filtrate_arro2.gpkg")
gdf.to_file(percorso_out, driver="GPKG")