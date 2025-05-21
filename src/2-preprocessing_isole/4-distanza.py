#importo le librerie
import geopandas as gp
import os
from pyproj import CRS, Transformer
import utm
from shapely.ops import transform
from rtree import index
from shapely import box

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto= os.path.join(cartella_corrente, "..", "..")

#importo i files gpkg delle isole di interesse
percorso_file = os.path.join(cartella_progetto, "data/isole_filtrate/filtro_popolazione", "isole_arro4.gpkg")
gdf = gp.read_file(percorso_file)

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
    buffer_utm = multi_utm.buffer(1000)
    multi_4326=transform(project_to_wgs84, buffer_utm)
    return multi_4326

#itero per le isole e creo i buffers
print(f'{len(gdf)} isole totali')
for k,(i,isl) in enumerate(gdf.iterrows(), 1):
    if k%100==0:
        print(f'{k} isole svolte')
    if k==len(gdf):
        print(f'{k} isole svolte')
    buffer=buffer_isl(gdf.loc[i,'geometry'])
    #controllo che l'isola non abbia sforato i confini del globo con l'operazione di buffer, in caso eseguo il buffer direttamente in wsg:4326
    if buffer.bounds[0]*buffer.bounds[2]>0:
        gdf.loc[i,'geometry']=buffer
    else:
        gdf.loc[i,'geometry']=gdf.loc[i,'geometry'].buffer(0.009)

#creo l'oggetto idx per facilitare la ricerca delle intersezioni
idx = index.Index()
for i, geom in enumerate(gdf.geometry):
    idx.insert(i, geom.bounds)

#importo le placche continentali
percorso_file = os.path.join(cartella_progetto, "files", "continents.gpkg")
gdf1 = gp.read_file(percorso_file)
print(f'isole prima del filtro distanza: {len(gdf)}')
#itero per i continenti
print(f'itero per le {len(gdf1)} plachhe continentali')
#contatore isole escluse
j=0
for k,(i,cont) in enumerate(gdf1.iterrows(),1):
    candidati=list(idx.intersection(cont.geometry.bounds))
    print(f'placca continentale {k}')
    print(f'isole da controllare: {len(candidati)}')
    h=0
    for cand in candidati:
        if h%100==0:
            print(f'{h} isole controllate')
        if h==(len(candidati)-1):
            print(f'{h+1} isole controllate')
        h+=1
        geom=gdf.loc[cand].geometry
        rect = box(geom.bounds[0], geom.bounds[1], geom.bounds[2], geom.bounds[3])
        #prima controllo che il rettangolo contenente l'isola intersechi il continente, operazione piu semplice
        #se non si intersecano non controllo nemmeno l'interszione della geometria vera e propria
        if rect.intersects(cont.geometry):
            if geom.intersects(cont.geometry):
                j+=1
                idx.delete(cand, gdf.loc[cand].geometry.bounds)
                gdf=gdf.drop(cand)
print(f'isole troppo vicine ai continenti: {j}')
print(f'isole rimanenti dopo il filtro: {len(gdf)}')

#importo le isole escluse per dimensioni eccessive
percorso_file = os.path.join(cartella_progetto, "data/isole_escluse", "isole_grandi.gpkg")
gdf1 = gp.read_file(percorso_file)
#itero per queste isole
print(f'itero per le {len(gdf1)} isole escluse in quanto troppo grandi')
#contatore isole escluse
j=0
for k,(i,isl) in enumerate(gdf1.iterrows(), 1):
    if k%5==0:
        print(f'{k} isole escluse controllate')
    if k==(len(gdf1)):
        print(f'{k} isole escluse controllate')
    candidati=list(idx.intersection(isl.geometry.bounds))
    for cand in candidati:
        geom=gdf.loc[cand].geometry
        if geom.intersects(isl.geometry):
            j+=1
            idx.delete(cand, geom.bounds)
            gdf=gdf.drop(cand)
print(f'isole troppo vicine a queste isole escluse: {j}')
print(f'isole rimanenti dopo il filtro: {len(gdf)}')

#importo le isole escluse per popolazione eccessiva
percorso_file = os.path.join(cartella_progetto, "data/isole_escluse", "isole_popolate.gpkg")
gdf1 = gp.read_file(percorso_file)
#itero per queste isole
print(f'itero per le {len(gdf1)} isole escluse in quanto troppo popolate')
#contatore isole escluse
j=0
for k,(i,isl) in enumerate(gdf1.iterrows(), 1):
    if k%10==0:
        print(f'{k} isole escluse controllate')
    if k==(len(gdf1)):
        print(f'{k} isole escluse controllate')
    candidati=list(idx.intersection(isl.geometry.bounds))
    for cand in candidati:
        geom=gdf.loc[cand].geometry
        if geom.intersects(isl.geometry):
            j+=1
            idx.delete(cand, geom.bounds)
            gdf=gdf.drop(cand)
print(f'isole troppo vicine a queste isole escluse: {j}')
print(f'isole rimanenti dopo il filtro: {len(gdf)}')

#esportazione gpkg
percorso_folder_out = os.path.join(cartella_progetto, "data/isole_filtrate/finali")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_out = os.path.join(percorso_folder_out, 'isole_arro4.gpkg')
gdf.to_file(percorso_out, driver="GPKG")

#salvo i codici delle isole conservate
codici=list(gdf.ALL_Uniq)

#aggiorno anche i dataframe con arrotondamenti diversi
percorso_file = os.path.join(cartella_progetto, "data/isole_filtrate/filtro_popolazione", "isole.gpkg")
gdf = gp.read_file(percorso_file)
print(f'lunghezza file originale: {len(gdf)}')
#elimino le isole se le ho eliminate in precedenza
for i,isl in gdf.iterrows():
    if isl.ALL_Uniq not in codici:
        gdf=gdf.drop(i)
print(f'lunghezza file dopo il filtro: {len(gdf)}')
#esportazione gpkg
percorso_out = os.path.join(cartella_progetto, "data/isole_filtrate/finali/isole.gpkg")
gdf.to_file(percorso_out, driver="GPKG")

percorso_file = os.path.join(cartella_progetto, "data/isole_filtrate/filtro_popolazione", "isole_arro3.gpkg")
gdf = gp.read_file(percorso_file)
print(f'lunghezza file originale: {len(gdf)}')
#elimino le isole se le ho eliminate in precedenza
for i,isl in gdf.iterrows():
    if isl.ALL_Uniq not in codici:
        gdf=gdf.drop(i)
print(f'lunghezza file dopo il filtro: {len(gdf)}')
#esportazione gpkg
percorso_out = os.path.join(cartella_progetto, "data/isole_filtrate/finali/isole_arro3.gpkg")
gdf.to_file(percorso_out, driver="GPKG")

percorso_file = os.path.join(cartella_progetto, "data/isole_filtrate/filtro_popolazione", "isole_arro2.gpkg")
gdf = gp.read_file(percorso_file)
print(f'lunghezza file originale: {len(gdf)}')
#elimino le isole se le ho eliminate in precedenza
for i,isl in gdf.iterrows():
    if isl.ALL_Uniq not in codici:
        gdf=gdf.drop(i)
print(f'lunghezza file dopo il filtro: {len(gdf)}')
#esportazione gpkg
percorso_out = os.path.join(cartella_progetto, "data/isole_filtrate/finali/isole_arro2.gpkg")
gdf.to_file(percorso_out, driver="GPKG")