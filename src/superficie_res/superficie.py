#importo le librerie
import geopandas as gp
import numpy as np
from shapely.ops import unary_union
import rasterio
import rasterio.mask
import rasterio.features
import pickle
import utm
import os

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")

#importo le isole
percorso_isl = os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2.gpkg")
gdfisl = gp.read_file(percorso_isl)
#applico un buffer nullo per rendere tutte le geometrie valide
gdfisl['geometry']=gdfisl.geometry.buffer(0)

#funzione che calcola l'area di una figura
def calcola_area_poligono(figura):
    lon, lat = figura.centroid.x, figura.centroid.y
    #individuo la zona utm per usare il sistema di coordinate appropriato, necessario per i calcoli di aree
    utm_zone = utm.from_latlon(lat, lon)
    utm_crs = f"EPSG:{32600 + utm_zone[2]}"
    gf = gp.GeoDataFrame(geometry=[figura], crs="EPSG:4326")
    gf = gf.to_crs(utm_crs)
    return gf.area.iloc[0]

#dizionario contenente le intersezioni tra le isole e le zone non agibili per res
poligoni={}

#definisco funzione che prende in input un geodataframe e calcola le intersezioni tra le sue forme e le varie isole.
#unisce i poligoni intersezioni delle isole ai poligoni delle isole nel dizionario
def intersezioni(gd):
    k=0
    #itero per le isole
    for ind,isl in gdfisl.iterrows():
        if k%10==0:
            print(k)
            print(len(gd))
        k+=1
        codice=isl.ALL_Uniq
        #lista con i poligoni intersecati dall'isola in questione
        poli=[]  
        #itero per il geodataframe in input 
        for ind1,el1 in gd.iterrows():
            if el1.geometry.intersects(isl.geometry):
                poli.append(el1.geometry.intersection(isl.geometry))
                gdf=gdf.drop(ind1)
        #unione dei poligoni
        unione=unary_union(poli)
        #unione con le altre aree dell'isola
        if codice not in poligoni:
            poligoni[codice]=unione
        else:
            poligoni[codice]=poligoni[codice].union(unione)

#importo il file con le aree urbane
percorso_urban = os.path.join(cartella_progetto, "files", "urban_isl.gpkg")
gdf = gpd.read_file(percorso_urban)
#applico un buffer nullo per rendere tutte le geometrie valide
gdf['geometry']=gdf.geometry.buffer(0)
intersezioni(gdf)

#importo i laghi
percorso_laghi = os.path.join(cartella_progetto, "files", "lakes_island.gpkg")
gdf = gp.read_file(percorso_laghi)
#applico un buffer nullo per rendere tutte le geometrie valide
gdf['geometry']=gdf.geometry.buffer(0)
intersezioni(gdf)

#importo le aree protette che sono divise in 3 files
percorso_pa = os.path.join(cartella_progetto, "files", "pa1.gpkg")
gdf = gp.read_file(percorso_pa)
#applico un buffer nullo per rendere tutte le geometrie valide
gdf['geometry']=gdf.geometry.buffer(0)
intersezioni(gdf)

percorso_pa = os.path.join(cartella_progetto, "files", "pa2.gpkg")
gdf = gp.read_file(percorso_pa)
#applico un buffer nullo per rendere tutte le geometrie valide
gdf['geometry']=gdf.geometry.buffer(0)
intersezioni(gdf)

percorso_pa = os.path.join(cartella_progetto, "files", "pa3.gpkg")
gdf = gp.read_file(percorso_pa)
#applico un buffer nullo per rendere tutte le geometrie valide
gdf['geometry']=gdf.geometry.buffer(0)
intersezioni(gdf)

#importo il file relativo alle pendenze, esprime per i vari pixel la percentuale di superficie all'interno del pixel con pendenza maggiore del 20%
percorso_pendenze = os.path.join(cartella_progetto, "files", "slope.asc")
src=rasterio.open(percorso_pendenze)
banda=src.read(1)
bounds = box(*src.bounds)
maxy=bounds.exterior.coords[1][1]
miny=bounds.exterior.coords[0][1]

#dizionari contenenti come chiavi il codice dell'isola e come valori la superficie res e la sua percentuale rispetto all'isola
aree_res={}
aree_res_rel={}
k=0
#itero per le isole
for ind,isl in gdfisl.iterrows():
    if k%100==0:
        print(k)
    k+=1
    codice=isl.ALL_Uniq
    #il multipoligono rappresenta le zone dell'isola che non appartengono a nessuno dei gruppi precedenti
    if codice not in poligoni:
        multipoligono=isl.geometry
    else:
        multipoligono=isl.geometry.difference(poligoni[codice])
    #l'elemento multipoligono potrebbe anche essere un poligono, in caso non dà problemi
    if multipoligono.geom_type=='MultiPolygon':
        for i in range(len(multipoligono.geoms)):
            #nel caso l'elemento fosse un lynestring che non va bene con il raster, in caso lo elimino
            if multipoligono.geoms[i].geom_type == 'LineString':
                multipoligono=multipoligono.difference(multipoligono.geoms[i])
    #limiti del  file slope, non copre l'intero globo
    if (((isl.geometry.bounds[1])>miny) & ((isl.geometry.bounds[3])<maxy)):
        out_image, out_transform = rasterio.mask.mask(src, [multipoligono], crop=True)
        out_image = out_image[0]
        maschera = rasterio.features.rasterize([multipoligono],
                                               out_shape=out_image.shape,
                                               transform=out_transform,
                                               fill=0,
                                               default_value=1)
        valori_poligono = out_image[maschera == 1]
        #calcolo la percentuale media di superficie con pendenza maggiore del 20% all'interno del multipoligono
        if valori_poligono.size > 0:
            perc_media = np.mean(valori_poligono)/100000 #raster con valori percentuali moltiplicati per mille
        else:
            perc_media=0
    else:
        perc_media=0
    area_isl=calcola_area_poligono(isl.geometry)
    area=calcola_area_poligono(isl.geometry)
    #sottraggo l'area delle zone non agibili per impianti res
    area-=calcola_area_poligono(multipoligono)
    #moltiplico l'area rimanente per la percentuale con pendenza accettabile
    area=area*(1-perc_media)
    aree_res[codice]=area/1000000 #conversione m^2 km^2
    aree_res_rel[codice]=((area/area_isl)*100)

#esportazione
percorso_folder_out = os.path.join(cartella_progetto, "data/dati_finali/sup_res")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_file=os.path.join(percorso_folder_out, "area_res.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(area_res, f)
percorso_file=os.path.join(percorso_folder_out, "area_res_rel.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(area_res_rel, f)