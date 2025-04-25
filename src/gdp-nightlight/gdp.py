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
cartella_progetto= os.path.join(cartella_corrente, "..", "..")

#importo dati elevazione
file_path=os.path.join(cartella_progetto, 'files', 'GDP.tif')
src = rasterio.open(file_path)

#importo coordinate isole
file_path=os.path.join(cartella_progetto, 'data/isole_filtrate', 'isole_filtrate2_arro4.gpkg')
gdf = gp.read_file(file_path)
print(len(gdf))

bounds = box(*src.bounds)
#dizionario da riempire con i codici come chiavi e gdp delle isole come valori
gdp={}
gdp_procapite={}
#dizionario da riempire con codici come chiavi e una lista composta da due elementi binari come valori
#il primo elemento mi dice se l'isola è completamente fuori dai bordi del file, il secondo se una sua parte lo è
isola_out={}
k=0
for ind,isl in gdf.iterrows():
    if k%200==0:
        print(k)
    k+=1
    codice=isl.ALL_Uniq
    multip=isl.geometry
    #isola fuori completamente bordi
    if multip.disjoint(bounds):
        isola_out[codice]=[1,1]
        gdp[codice]=np.nan
        gdp_procapite[codice]=np.nan
    else:
        #isola completamente dentro i bordi
        if multip.within(bounds):
            lista=[0,0]
        else:
            lista=[0,1]
        isola_out[codice]=lista
        out_image, out_transform = rasterio.mask.mask(src, [mapping(multip)], crop=True)
        no_data_value = src.nodata
        valid_pixels = out_image[out_image != no_data_value]
        sum = np.sum(valid_pixels)
        gdp[codice]=sum
        gdp_procapite[codice]=sum/isl.Popolazione

#esportazione
folder_path=os.path.join(cartella_progetto, 'data/dati_finali/gdp_nightlight')
os.makedirs(folder_path, exist_ok=True)
file_path=os.path.join(folder_path, "gdp.pkl")
with open(file_path, "wb") as f:
    pickle.dump(gdp, f)
file_path=os.path.join(folder_path, 'gdp_procapite.pkl')
with open(file_path, "wb") as f:
    pickle.dump(gdp_procapite, f)
file_path=os.path.join(folder_path, 'gdp_nodata.pkl')
with open(file_path, "wb") as f:
    pickle.dump(isola_out, f)