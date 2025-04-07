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

#importo dati potenza del vento
percorso_file= os.path.join(cartella_progetto, "files/raw", "power_density.tif")
src = rasterio.open(percorso_file)
#bordi del file
bounds = box(*src.bounds)
maxx=bounds.exterior.coords[0][0]
minx=bounds.exterior.coords[2][0]
maxy=bounds.exterior.coords[1][1]
miny=bounds.exterior.coords[0][1]

#importo dati isole
percorso_file=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2_arro2.gpkg")
gdf = gp.read_file(percorso_file)

#funzione che prende in input isola e raster e riporta il valore medio
def media(multipoligono,sr):
    out_image, out_transform = rasterio.mask.mask(sr, [mapping(multipoligono)], crop=True)
    no_data_value = src.nodata
    valid_pixels = out_image[out_image != no_data_value]
    mean = np.mean(valid_pixels)
    return mean

power_mean={} #dizionario con codici come chiavi e potenza media come valori
#dizionario con codici come chiavi e lista di due binari come valori
#il primo valore pari a 1 indica che l'isola si trova tutta fuori dai limiti 65, -60 e non si hanno dati
#il secondo valore pari a 1 indica che almeno un punto si trova fuori dai limiti
isola_out={}
k=0
for i,isl in gdf.iterrows():
    if k%100==0:
        print(k)
    k+=1
    codice=isl.ALL_Uniq
    multi=isl.geometry
    if multi.disjoint(bounds):
        power_mean[codice]=np.nan
        isola_out[codice]=[1,1]
    else:
        out,var=richiesta(multi)
        power_mean[codice]=out
        if multi.within(bounds):
            isola_out[codice]=[0,0]
        else:
            isola_out[codice]=[0,1]

#esportazione
percorso_folder_out = os.path.join(cartella_progetto, "data/dati_finali/eolico")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_file=os.path.join(percorso_folder_out, "wind_pow.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(power_mean, f)
percorso_file= os.path.join(percorso_folder_out, "wind_nodata.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(isola_out, f)