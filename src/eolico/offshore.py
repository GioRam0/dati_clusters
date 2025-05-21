#importo librerie
import geopandas as gp
import numpy as np
import os
import pickle
from rtree import index
from shapely.geometry import Polygon, MultiPolygon
import utm
from affine import Affine
import rasterio
from rasterio.features import rasterize

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto= os.path.join(cartella_corrente, "..", "..")
#importo le isole con buffer
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate/finali", "isole_buffer.gpkg")
gdf = gp.read_file(isl_path)
#importo il dizionario con le nazioni delle isole
percorso_pkl=os.path.join(cartella_progetto, "data/isole_filtrate", "nazioni.pkl")
with open(percorso_pkl, 'rb') as file:
    nazioni_isole = pickle.load(file)

#creo un dizionario per risolvere il problema delle nazioni scritte in modo diverso tra il pkl e i files offshore
traduttore_nomi_nazioni={
    'Republic of Korea': 'South Korea',
    "Dem People's Rep of Korea" : "North Korea",
    "Viet Nam" : "Vietnam",
    "Kuril islands" : "Russia",
    "Russian Federation" : "Russia",
    "U.K. of Great Britain and Northern Ireland" : "United Kingdom",
    "Svalbard and Jan Mayen Islands" : "Svalbard",
    "Faroe Islands" : "Denmark",
    "Isle of Man" : "United Kingdom",
    "Jersey" : "United Kingdom",
    "Guernsey" : "United Kingdom",
    "Turks and Caicos islands" : "United Kingdom",
    "Btates Virgin Islands" : "United Kingdom",
    "United States Virgin Islands" : "United States",
    "United States of America" : "United States",
    'Guadeloupe' : "France",
    "Anguilla" : "United Kingdom",
    "Netherlands Antilles" : "Netherlands",
    "Aruba" : "Netherlands",
    "Montserrat" : "United Kingdom",
    "Saint Pierre et Miquelon" : "France",
    "Somalia" : "Federal Republic of Somalia",
    "Mauritius" : "Republic of Mauritius",
    "Northern Mariana Islands" : "United States",
    "Guam" : "United States",
    "Azores Islands" : "Azores"
    }

#definisco funzioni per riproiettare le figure e calcolarne l'area
def riproietta_poligono(figura, utm_crs=0):
    #individuo la zona utm se non data in input
    if utm_crs==0:
        lon, lat = figura.centroid.x, figura.centroid.y
        utm_zone = utm.from_latlon(lat, lon)
        utm_crs = f"EPSG:{32600 + utm_zone[2]}"
    gf = gp.GeoDataFrame(geometry=[figura], crs="EPSG:4326")
    gf = gf.to_crs(utm_crs)
    return gf.iloc[0]['geometry'],utm_crs
def calcola_area_poligono(figura):
    gf = gp.GeoDataFrame(geometry=[figura])
    return gf.area.iloc[0]

#dizionario da riempire
offshore={elemento: 0 for elemento in list(gdf.ALL_Uniq)}

#definisco la funzione contenente tutto da applicare ai vari files .shp, la stringa rappresenta il nome del file
def funzione(stringa):
    print(f'analizzo il file: {stringa}')
    path= os.path.join(cartella_progetto, "files\offshore", stringa)
    gdf1=gp.read_file(path)
    #inizializzo una lista vuota per ogni shape offshore
    gdf1["isole_associate"] = [[] for _ in range(len(gdf1))]

    #shape attraversate dal meridiano 180 la cui geometria risulta alterata, le trasformo in multipoligoni con una parte oltre i 180 e una ripetuta oltre i -180 in modo da intersecare, eventualmente, sia le isole allargate oltre il 180 che oltre il -180
    if stringa=="eap\FixedFoundation.shp":
        lista_punti1=list(gdf1.loc[10482,'geometry'].exterior.coords)
        lista_punti2=list(gdf1.loc[10482,'geometry'].exterior.coords)
        for h in range(len(lista_punti1)):
            if lista_punti1[h][0]>0:
                lista_punti1[h]=(lista_punti1[h][0]-360,lista_punti1[h][1])
            else:
                lista_punti2[h]=(lista_punti2[h][0]+360,lista_punti2[h][1])
        poli1=Polygon(lista_punti1)
        poli2=Polygon(lista_punti2)
        gdf1.loc[10482,'geometry']=MultiPolygon([poli1,poli2])
    if stringa=="eap\FloatingFoundation.shp":
        lista_indici=[5271,6073,6124,6137,6405]
        for i in lista_indici:
            shape=gdf1.loc[i,'geometry']
            if type(shape)==Polygon:
                #i poligoni con vertici sia da un lato che dall'altro li duplico a est e ovest
                lista_punti1=list(shape.exterior.coords)
                lista_punti2=list(shape.exterior.coords)
                for h in range(len(lista_punti1)):
                    if lista_punti1[h][0]>0:
                        lista_punti1[h]=(lista_punti1[h][0]-360,lista_punti1[h][1])
                    else:
                        lista_punti2[h]=(lista_punti2[h][0]+360,lista_punti2[h][1])
                poli1=Polygon(lista_punti1)
                poli2=Polygon(lista_punti2)
                gdf1.loc[i,'geometry']=MultiPolygon([poli1,poli2])
            #stesso discorso per i multipoligoni, discorso ripetuto per tutti i poligoni contenuti
            if type(shape)==MultiPolygon:
                lista_poli=list(shape.geoms)
                for k in range(len(lista_poli)):
                    if lista_poli[k].bounds[0]*lista_poli[k].bounds[2]<0:
                        lista_punti1=list(lista_poli[k].exterior.coords)
                        lista_punti2=list(lista_poli[k].exterior.coords)
                        for h in range(len(lista_punti1)):
                            if lista_punti1[h][0]<0:
                                lista_punti1[h]=(lista_punti1[h][0]+360,lista_punti1[h][1])
                            else:
                                lista_punti2[h]=(lista_punti2[h][0]-360,lista_punti2[h][1])
                        lista_poli[k]=Polygon(lista_punti1)
                        lista_poli.append(Polygon(lista_punti2))
                gdf1.loc[i,'geometry']=MultiPolygon(lista_poli)
    #elimino delle geometrie degenerate che non saprei come sistemare
    if stringa==r"na\FloatingFoundation.shp":
        lista_indici=[176,180]
        for i in lista_indici:
            gdf1.drop(index=i, inplace=True)
                    
    #creo un oggetto index per facilitare le iterazioni geometriche, contiene le shapes dell'offshore
    idx = index.Index()
    for i, row in gdf1.iterrows():
        bbox = row.geometry.bounds
        idx.insert(i, bbox)
    #itero per le isole per associarle alle varie shapes
    for i,isl in gdf.iterrows():
        codice=isl.ALL_Uniq
        multi=isl.geometry
        bbox_isola = multi.bounds
        zone_candidate = list(idx.intersection(bbox_isola))
        #itero per le shapes che potrebbero intersecare l'isola
        for h in zone_candidate:
            shape=gdf1.loc[h]
            #applico un buffer 0 nel caso la geometria risultasse invalida
            geom_shape=shape.geometry.buffer(0)
            #considero solo gli shape con potenza positiva
            if shape.InstallCap>0:
                if multi.intersects(geom_shape):
                    a=False
                    #se almeno una nazione dell'isola corrisponde a quella della shape salvo la loro associazione
                    for country in nazioni_isole[codice]:
                        #traduzione nome nazione se necessaria
                        if country in traduttore_nomi_nazioni:
                            country=traduttore_nomi_nazioni[country]
                        #due files hanno le colonne con titolo diverso
                        if stringa == r"na\FloatingFoundation.shp" or stringa == "sa\FloatingFoundation.shp":
                            if country == shape.TERRITORY1 or country == shape.SOVEREIGN1:
                                a=True
                            if shape.TERRITORY1==None or shape.SOVEREIGN1==None:
                                a=True
                        else:
                            if country == shape.Territory1 or country == shape.Sovereign1:
                                a=True
                            if shape.Territory1==None or shape.Sovereign1==None:
                                a=True
                    if a:
                        #aggiungo l'indice alla lista della shape
                        gdf1.loc[h,'isole_associate'].append(i)
    #itero per le varie shapes offshore
    print(f'shapes da analizzare: {len(gdf1)}')
    for cont,(j,shape) in enumerate(gdf1.iterrows(),1):
        if cont%1000==0 or cont==len(gdf1):
            print(f'shapes analizzate: {cont}')
        indici_isole=shape.isole_associate
        if indici_isole != []:
            #calcolo l'area della shape offshore
            shape_ripro,crs=riproietta_poligono(shape.geometry)
            #applico un buffer 0 nel caso la geometria risultasse invalida
            shape_ripro=shape_ripro.buffer(0)
            area_shape=calcola_area_poligono(shape_ripro)
            #calcolo il poligono unione delle isole associate alla shape e calcolo la sua intersezione con la shape
            unione_isole=gdf.loc[indici_isole[0],'geometry']
            if len(indici_isole)>1:
                for h in range(1,len(indici_isole)):
                    unione_isole=unione_isole.union(gdf.loc[indici_isole[h],'geometry'])
            unione_isole=riproietta_poligono(unione_isole, crs)[0]
            #applico un buffer 0 nel caso la geometria risultasse invalida
            unione_isole=unione_isole.buffer(0)
            #calcolo la sua intersezione con la shape e l'area dell'intersezione
            unione_isole=unione_isole.intersection(shape_ripro)
            area_unione=calcola_area_poligono(unione_isole)
            #calcolo la potenza totale per le isole come rapporto tra area dell'unione e area della shape moltiplicata per tutta la potenza installabile
            pot_isole=shape.InstallCap*(area_unione/area_shape)
            #se le isole associate sono una o due ripartisco manualmente la potenza senza applicare la maschera per risparmiare calcoli
            if len(indici_isole)==1:
                codice=gdf.loc[indici_isole[0],'ALL_Uniq']
                offshore[codice]+=pot_isole
            elif len(indici_isole)==2:
                isola1=riproietta_poligono(gdf.loc[indici_isole[0],'geometry'])[0]
                isola2=riproietta_poligono(gdf.loc[indici_isole[1],'geometry'])[0]
                inte=isola1.intersection(isola2)
                codice1=gdf.loc[indici_isole[0],'ALL_Uniq']
                codice2=gdf.loc[indici_isole[1],'ALL_Uniq']
                rapporto1=(calcola_area_poligono(isola1)-(calcola_area_poligono(inte)/2))/area_unione
                rapporto2=(calcola_area_poligono(isola2)-(calcola_area_poligono(inte)/2))/area_unione
                offshore[codice1]+=pot_isole*rapporto1
                offshore[codice2]+=pot_isole*rapporto2
            else:
                if area_unione>100:
                    #creo un raster che conta quante isole contengono ogni pixel del poligono unione_isole
                    minx, miny, maxx, maxy = unione_isole.bounds
                    res = 10 #risoluzione in metri
                    #con isole grandi altrimenti diventa troppo lungo
                    if area_shape>1000000:
                        res=20
                    if area_shape>5000000:
                        res=40
                    if area_shape>50000000:
                        res=200
                    width = max(int((maxx - minx) / res),1)
                    height = max(int((maxy - miny) / res),1)
                    transform = Affine.translation(minx, miny) * Affine.scale(res, res)
                    #inizializzo la maschera
                    counts = np.zeros((height, width), dtype=np.uint8)
                    #itero per le isole considerate e creo una maschera di pixel pari a 1 per l'isola, poi la sommo al raster count
                    for ind in range(len(indici_isole)):
                        isola=riproietta_poligono(gdf.loc[indici_isole[ind],'geometry'])[0].intersection(shape_ripro)
                        if (calcola_area_poligono(isola))>0:
                            mask = rasterize(
                                [(isola, 1)],
                                out_shape=(height, width),
                                transform=transform,
                                fill=0,
                                all_touched=True,
                                dtype=np.uint8
                            )
                            counts += mask
                    #creo un nuovo raster con valori pari all'inverso del counts
                    #un valore 1/3 indica che quel pixel deve essere ripartito tra 3 isole
                    #cosi riesco  ripartire le intersezioni
                    result = np.zeros_like(counts, dtype=np.float32)
                    mask = counts > 0
                    result[mask] = 1.0 / counts[mask]
                    total_pixels=np.count_nonzero(result)
                    if total_pixels>0:
                        for ind in range(len(indici_isole)):
                            isola=riproietta_poligono(gdf.loc[indici_isole[ind],'geometry'],crs)[0]
                            codice=gdf.loc[indici_isole[ind],'ALL_Uniq']
                            #creo una maschera dell'isola, la applico a result e sommo i pixel
                            mask_isola = rasterize(
                                [(isola, 1)],
                                out_shape=(height, width),
                                transform=transform,
                                fill=0,
                                all_touched=True,
                                dtype=np.uint8
                            )
                            #applico la maschera al raster results e sommo i valori dei pixels contenuti
                            valori_isola = result[mask_isola > 0]
                            isl_pixels=np.sum(valori_isola)
                            #rapporto tra superficie appartenente all'isola e shape, criterio per assegnare la potenza della shape all'isola
                            rapporto=isl_pixels/total_pixels
                            offshore[codice]+=pot_isole*rapporto

shape_files=["eap\FixedFoundation.shp",
            "eap\FloatingFoundation.shp",          
            "eca\FixedFoundation.shp",
            "eca\FloatingFoundation.shp",
            "lac\FixedFoundation.shp",
            "lac\FloatingFoundation.shp",
            "mena\FixedFoundation.shp",
            "mena\FloatingFoundation.shp",
            r"na\FixedFoundation.shp",
            r"na\FloatingFoundation.shp",
            "sa\FixedFoundation.shp",
            "sa\FloatingFoundation.shp",
            "ssa\FixedFoundation.shp",
            "ssa\FloatingFoundation.shp"
            ]
for str in shape_files:
    funzione(str)

#esportazione
percorso_folder_out = os.path.join(cartella_progetto, "data/dati_finali/eolico")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_file=os.path.join(percorso_folder_out, "offshore.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(offshore, f)