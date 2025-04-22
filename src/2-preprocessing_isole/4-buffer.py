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
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2.gpkg")
gdf = gp.read_file(isl_path)

#lista ALL_Uniq di isole troppo vicine ai bordi 180, -180. applicando il buffer in coordinate utm e riconvertendo in 4326 il poligono diventerebbe una striscia. applico un buffer direttamente in 4326
lista=[292365,282309,277208, 274415, 282454,274143,344028,277249,274142,347209,347210,344026]

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
    project_to_utm = lambda x, y: transformer_dir.transform(x, y)
    project_to_wgs84 = lambda x, y: transformer_inv.transform(x, y)
    multi_utm = transform(project_to_utm, multi)
    buffer_utm = multi_utm.buffer(20000)
    multi_4326=transform(project_to_wgs84, buffer_utm)
    return multi_4326

print(len(gdf))
k=0
for i,isl in gdf.iterrows():
    if k%200==0:
        print(k)
    k+=1
    if isl.ALL_Uniq in lista:
        gdf.loc[i,'geometry']=gdf.loc[i,'geometry'].buffer(0.18)
    else:
        gdf.loc[i,'geometry']=buffer_isl(gdf.loc[i,'geometry'])

#esportazione gpkg
percorso_folder_out = os.path.join(cartella_progetto, "data/isole_filtrate")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_out=os.path.join(percorso_folder_out, "isole_buffer.gpkg")
gdf.to_file(percorso_out, driver="GPKG")