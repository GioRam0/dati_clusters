#importo le librerie
import rasterio
import rasterio.mask
from shapely.geometry import box, mapping
import numpy as np
import geopandas as gp
import pickle
import os

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")

#importo dati solari
#annuali
percorso_file= os.path.join(cartella_progetto, "files", "PVOUT_year.tif")
src = rasterio.open(percorso_file)
#bordi del file
bounds = box(*src.bounds)
maxx=bounds.exterior.coords[0][0]
minx=bounds.exterior.coords[2][0]
maxy=bounds.exterior.coords[1][1]
miny=bounds.exterior.coords[0][1]
print(maxx, minx, maxy, miny)

#importo dati isole
percorso_file=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate_tot.gpkg")
gdf = gp.read_file(percorso_file)
gdf=gdf[(gdf['IslandArea']<10000)]

#funzione che prende in input isola e riporta il pvout medio
def media(multipoligono):
    out_image, out_transform = rasterio.mask.mask(src, [mapping(multipoligono)], crop=True)
    no_data_value = src.nodata
    valid_pixels = out_image[out_image != no_data_value]
    mean = np.mean(valid_pixels)
    return mean

pvout_mean={} #dizionario con codici come chiavi e insolazione media come valori
#dizionario con codici come chiavi e lista di due binari come valori
#il primo valore pari a 1 indica che l'isola si trova tutta fuori dai limiti 65, -60 e non si hanno dati
#il secondo valore pari a 1 indica che almeno un punto si trova fuori dai limiti
isola_out={}
k=0
print(len(gdf))
for i,isl in gdf.iterrows():
    if k%100==0:
        print(k)
    k+=1
    codice=isl.ALL_Uniq
    multi=isl.geometry
    if multi.disjoint(bounds):
        pvout_mean[codice]=np.nan
        isola_out[codice]=[1,1]
    else:
        out=media(multi)
        pvout_mean[codice]=out
        if multi.within(bounds):
            isola_out[codice]=[0,0]
        else:
            isola_out[codice]=[0,1]
percorso_file=os.path.join(cartella_corrente, "solar_pow.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(pvout_mean, f)
percorso_file=os.path.join(cartella_corrente, "nodata.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(isola_out, f)
