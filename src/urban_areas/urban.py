#importo librerie
import geopandas as gpd
from shapely.ops import unary_union
import pickle
import os
import utm

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")

#importo il file con le aree urbane
percorso_urban = os.path.join(cartella_progetto, "files", "urban_isl.gpkg")
gdfurb = gpd.read_file(percorso_urban)
#applico un buffer nullo per rendere tutte le geometrie valide
gdfurb.geometry=gdfurb.geometry.buffer(0)

#funzione che calcola l'area di una figura
def calcola_area_poligono(figura):
    lon, lat = figura.centroid.x, figura.centroid.y
    #individuo la zona utm per usare il sistema di coordinate appropriato, necessario per i calcoli di aree
    utm_zone = utm.from_latlon(lat, lon)
    utm_crs = f"EPSG:{32600 + utm_zone[2]}"
    gf = gp.GeoDataFrame(geometry=[figura], crs="EPSG:4326")
    gf = gf.to_crs(utm_crs)
    return gf.area.iloc[0]

#importo le isole
percorso_isl = os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2.gpkg")
gdfisl = gp.read_file(percorso_isl)
#applico un buffer nullo per rendere tutte le geometrie valide
gdfisl['geometry']=gdfisl.geometry.buffer(0)

#dizionario da riempire con i codici isole come chiavi e le aree urbane delle isole come valori
urban_areas={}
#dizionario da riempire con i codici isole come chiavi e la percentuale di aree urbane delle isole come valori
rel_urban_areas={}
#itero per le isole
k=0
for ind,isl in gdfisl.iterrows():
    if k%10==0:
        print(k)
    k+=1
    codice=isl.ALL_Uniq
    area=isl.IslandArea
    urb=[] 
    #itero per le aree urbane   
    for ind1,el1 in gdfurb.iterrows():
        if el1.geometry.intersects(isl.geometry):
            urb.append(el1.geometry.intersection(isl.geometry))
            gdfurb=gdfurb.drop(ind1)
    if urb!=[]:
        area_urb=calcola_area_poligono(unary_union(urb))
        urban_areas[codice]=area_urb
        rel_urban_areas[codice]=area_urb/(area*10000) #fattore inserito per compensare unita di misura diverse e calcolare una percentuale
    else:
        urban_areas[codice]=0
        rel_urban_areas[codice]=0

#esportazione
percorso_folder_out = os.path.join(cartella_progetto, "data/dati_finali/urban")
percorso_out = os.path.join(percorso_folder_out, "urban_areas.pkl")
with open(percorso_out, "wb") as f:
    pickle.dump(urban_areas, f)
percorso_out = os.path.join(percorso_folder_out, "urban_areas_rel.pkl")
with open(percorso_out, "wb") as f:
    pickle.dump(rel_urban_areas, f)