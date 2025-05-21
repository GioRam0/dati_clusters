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
file_path=os.path.join(cartella_progetto, 'files', 'gdp_2020.tif')
src = rasterio.open(file_path)

#importo coordinate isole
file_path=os.path.join(cartella_progetto, 'data/isole_filtrate/finali', 'isole_arro4.gpkg')
gdf = gp.read_file(file_path)
#confini del file
bounds = box(*src.bounds)
#dizionario da riempire con i codici come chiavi e gdp delle isole come valori
gdp={}
gdp_pro_capite={}
#dizionario da riempire con codici come chiavi e una lista composta da due elementi binari come valori
#il primo elemento mi dice se l'isola è completamente fuori dai bordi del file, il secondo se una sua parte lo è
isola_out={}

#itero per le isole
print(f'isole da svolgere: {len(gdf)}')
for k,(ind,isl) in enumerate(gdf.iterrows(),1):
    if k%250==0 or k==len(gdf):
        print(f'{k} isole analizzate')
    codice=isl.ALL_Uniq
    multip=isl.geometry
    popolazione = isl.Popolazione
    #isola fuori completamente bordi
    if multip.disjoint(bounds):
        isola_out[codice]=[1,1]
        gdp[codice]=np.nan
        gdp_pro_capite[codice]=np.nan
    else:
        #isola completamente dentro i bordi
        if multip.within(bounds):
            lista=[0,0]
        #isola parzialmente fuori
        else:
            lista=[0,1]
        isola_out[codice]=lista
        out_image, out_transform = rasterio.mask.mask(src, [mapping(multip)], crop=True, all_touched=True)
        no_data_value = src.nodata
        valid_pixels = out_image[out_image != no_data_value]
        #sommo i valori interni ottenendo il gdp dell'isola
        sum = np.sum(valid_pixels)
        gdp[codice]=sum
        gdp_pro_capite[codice]=sum/popolazione

#esportazione
folder_path=os.path.join(cartella_progetto, 'data/dati_finali/gdp')
os.makedirs(folder_path, exist_ok=True)
file_path=os.path.join(folder_path, "gdp.pkl")
with open(file_path, "wb") as f:
    pickle.dump(gdp, f)
file_path=os.path.join(folder_path, "gdp_pro_capite.pkl")
with open(file_path, "wb") as f:
    pickle.dump(gdp_pro_capite, f)
file_path=os.path.join(folder_path, 'gdp_nodata.pkl')
with open(file_path, "wb") as f:
    pickle.dump(isola_out, f)