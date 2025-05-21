#importo librerie
import geopandas as gp
from shapely.ops import transform
import os
from pyproj import CRS, Transformer
import utm

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto= os.path.join(cartella_corrente, "..", "..")
#importo coordinate isole
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate/finali", "isole.gpkg")
gdf = gp.read_file(isl_path)

crs_4326 = CRS.from_epsg(4326)
#funzione per generare il buffer
def buffer_isl(multi):
    lon, lat = multi.centroid.x, multi.centroid.y
    #individuo la zona utm per usare il sistema di coordinate appropriato
    utm_zone = utm.from_latlon(lat, lon)
    utm_crs = 32600 + utm_zone[2]
    crs_m = CRS.from_epsg(utm_crs)
    transformer_dir = Transformer.from_crs(crs_4326, crs_m, always_xy=True)
    transformer_inv = Transformer.from_crs(crs_m, crs_4326, always_xy=True)
    #funzione di conversione delle coordinate
    project_to_utm = lambda x, y: transformer_dir.transform(x, y)
    project_to_wgs84 = lambda x, y: transformer_inv.transform(x, y)
    #trasformo, applico il buffer e riconverto
    multi_utm = transform(project_to_utm, multi)
    buffer_utm = multi_utm.buffer(60000)
    multi_4326=transform(project_to_wgs84, buffer_utm)
    return multi_4326

print(f'lunghezza del file: {len(gdf)}')
for k,(i,isl) in enumerate(gdf.iterrows(), 1):
    if k%500==0 or k==len(gdf):
        print(f'{k} isole svolte')
    #applico la funzione buffer
    buffer=buffer_isl(gdf.loc[i,'geometry'])
    #controllo che con il buffer l'isola non sconfini il globo creando una geomteria non valida
    if buffer.bounds[0]*buffer.bounds[2]>0:
        gdf.loc[i,'geometry']=buffer
    #in caso lo facesse applico il buffer direttamente in epsg:4326
    else:
        gdf.loc[i,'geometry']=gdf.loc[i,'geometry'].buffer(0.54)

#esportazione gpkg
percorso_folder_out = os.path.join(cartella_progetto, "data/isole_filtrate/finali")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_out=os.path.join(percorso_folder_out, "isole_buffer.gpkg")
gdf.to_file(percorso_out, driver="GPKG")