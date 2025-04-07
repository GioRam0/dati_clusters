#importo librerie
import rasterio
import rasterio.mask
import geopandas as gp
import pickle
import os

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto= os.path.join(cartella_corrente, "..", "..")

#importo dati elevazione
file_path=os.path.join(cartella_progetto, 'files', 'ELE.tif')
src = rasterio.open(file_path)

#importo coordinate isole
file_path=os.path.join(cartella_progetto, 'data/isole_filtrate', 'isole_filtrate2_arro2ext.gpkg')
gdf = gp.read_file(file_path)

transform = src.transform
width, height = src.width, src.height
xmin, ymax = transform * (0, 0)
xmax, ymin = transform * (width, height)

elevazioni={} #dizionario con codici come chiavi e elevazioni max come valori
#dizionario con codici come chiavi e lista di due binari come valori
#il primo valore pari a 1 indica che l'isola si trova tutta fuori dai limiti e non si hanno dati
#il secondo valore pari a 1 indica che almeno un punto si trova fuori dai limiti
isl_out={}
k=0
for ind,isl in gdf.iterrows():
    if k%100==0:
        print(k)
        k+=1
    codice=isl.ALL_Uniq
    multip=isl.geometry
    bounds = multip.bounds
    #limite inferiore >max o indice inferiore < min, tutta isola fuori
    if((bounds[1]>ymax) or (bounds[3]<ymin)):
        isola_out[codice]=[1,1]
        elevazioni[codice]=np.nan
    else:
        #parte isola fuori
        if ((bounds[3]>ymax) or (bounds[1]<ymin)):
            isola_out[codice]=[0,1]
        else:
            isola_out[codice]=[0,0]
        out_image, out_transform = rasterio.mask.mask(src, [mapping(multip)], crop=True)
        no_data_value = src.nodata
        valid_pixels = out_image[out_image != no_data_value]
        ele = np.max(valid_pixels)
        elevazioni[codice]=ele

#esportazione
folder_path=os.path.join(cartella_progetto, 'data/data_finali/elevazione_temepratura')
os.makedirs(percorso_folder_out, exist_ok=True)
file_path=os.path.join(folder_path, "ele_max.pkl")
with open(file_path, "wb") as f:
    pickle.dump(elevazioni, f)
file_path=os.path.join(folder_path, 'ele_nod.pkl')
with open(file_path, "wb") as f:
    pickle.dump(isola_out, f)