#importo le librerie
import geopandas as gp
import os
import sys
import rasterio
import rasterio.mask
from shapely.geometry import mapping
import numpy as np

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")

# percorso completo per il file .gpkg
percorso_file = os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate_arro4.gpkg")
gdf = gp.read_file(percorso_file)
print(len(gdf))

#importo file con dati popolazione,ha copertura globale
path_pop=os.path.join(cartella_progetto, "files", "popolazione.tif")
src = rasterio.open(path_pop)

#inizializzo le nuove colonne
gdf['Popolazione']=np.zeros(len(gdf))
gdf['Densità_pop']=np.zeros(len(gdf))

k=0
for i,isl in gdf.iterrows(): #itero per le isole
    if k%100==0:
        print(k)
    k+=1
    multip=isl.geometry
    out_image, out_transform = rasterio.mask.mask(src, [mapping(multip)], crop=True)
    no_data_value = src.nodata
    valid_pixels = out_image[out_image != no_data_value]
    #sommo i valori dei pixel all'interno del multipoligono ottenendo la popolazione dell'isola e la appendo alla lista
    pop_isola = np.sum(valid_pixels)
    gdf.loc[i,'Popolazione']=pop_isola
    gdf.loc[i,'Densità_pop']=pop_isola/gdf.loc[i,'IslandArea']

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo le variabili config
import config
min_pop = config.MIN_POPOLAZIONE
max_pop = config.MAX_POPOLAZIONE
#filtro
gdf=gdf[(gdf['Popolazione']>=min_pop) & (gdf['Popolazione']<=max_pop)]
print(len(gdf))

#esportazione gpkg
percorso_out = os.path.join(cartella_progetto, "data/isole_filtrate/isole_filtrate2_arro4.gpkg")
gdf.to_file(percorso_out, driver="GPKG")

#ripeto il filtro ed esporto anche per il file con coordinate non arrotondate, piu pesante
codici=list(gdf.ALL_Uniq)
# percorso completo per il file .gpkg
percorso_file = os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate.gpkg")
gdf = gp.read_file(percorso_file)
print(len(gdf))
#elimino le isole se le ho eliminate in precedenza
for i,isl in gdf.iterrows():
    if isl.ALL_Uniq not in codici:
        gdf=gdf.drop(i)
print(len(gdf))

#esportazione gpkg
percorso_out = os.path.join(cartella_progetto, "data/isole_filtrate/isole_filtrate2.gpkg")
gdf.to_file(percorso_out, driver="GPKG")