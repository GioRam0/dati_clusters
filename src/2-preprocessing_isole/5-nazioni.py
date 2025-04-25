#importo librerie
import geopandas as gp
import ee
import os
import sys
import pickle
from shapely.geometry import LineString
from shapely.ops import split

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")

#importo coordinate isole
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2_arro4.gpkg")
gdf = gp.read_file(isl_path)

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo la variabile project
import config
proj = config.proj
ee.Initialize(project=proj)

#importo le features dei paesi
paesi = ee.FeatureCollection('FAO/GAUL_SIMPLIFIED_500m/2015/level0')

#se gia presenti (effettuata una precedente run ma interrotta) importo i dati precedentemente scaricati per non ricominciare
output_folder = os.path.join(cartella_progetto, "data/isole_filtrate")
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, "nazioni.pkl")
if os.path.exists(output_path):
    with open(output_path, 'rb') as file:
        countries = pickle.load(file)
#se non presenti inizializzo i dizionari
else:
    countries={}
    #isole controllate manualmente per intersezioni non riconosciute
    countries[88882]=['Maldives']
    countries[89785]=['Bangladesh']
    countries[89792]=['Bangladesh']
    countries[89794]=['Bangladesh']
    countries[89937]=['Pakistan']
    countries[90195]=['China']
    countries[90433]=['Republic of Korea']
    countries[277103]=['Brazil']
    countries[277105]=['Brazil']
    countries[277239]=['Fiji']
    countries[277594]=['Indonesia']
    countries[277763]=['Indonesia']
    countries[280098]=['Bangladesh']
    countries[280538]=['Viet Nam']
    countries[280549]=['Viet Nam']
    countries[280552]=['Viet Nam']
    countries[280664]=['China']
    countries[283115]=['Solomon Islands']
    countries[283862]=['Indonesia']
    countries[289686]=['Viet Nam']
    countries[290776]=['Norway']
    countries[340640]=['China']
    countries[340642]=['China']
    countries[370285]=['Viet Nam']
    countries[273766]=['Russian Federation']
    countries[273776]=['Australia']
    countries[273771]=['Canada']
#itero per le isole
j=0
for i,isl in gdf.iterrows():
    if j%10==0:
        print(j)
        output_path=os.path.join(output_folder, "nazioni.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(countries, f)
    j+=1
    codice=isl.ALL_Uniq
    if codice not in countries:
        multi=isl.geometry
        #suddivido un poligono grande per problemi di calcoli
        if isl.IslandArea>40000:
            print(isl)
            print(isl.Shape_Leng)
            nomi_paesi=[]
            for i in range(len(multi.geoms)):
                poli=multi.geoms[i]
                centroid=poli.centroid
                minx, miny, maxx, maxy = poli.bounds
                line=LineString([(centroid.x, miny - 1), (centroid.x, maxy + 1)])
                split_polygons = split(poli, line)
                for i in range(len(split_polygons.geoms)):
                    poli1=split_polygons.geoms[i]
                    poli_list=[list(vertice) for vertice in poli1.exterior.coords]
                    ee_geometry = ee.Geometry.Polygon(poli_list)
                    #trovo paesi intersezione
                    paesi_contenenti = paesi.filterBounds(ee_geometry)
                    for paese in paesi_contenenti.aggregate_array('ADM0_NAME').getInfo():
                        if paese not in nomi_paesi:
                            nomi_paesi.append(paese)
            countries[codice]=nomi_paesi
        else:
            multip_list =[ 
                    [list(vertice) for vertice in poligono.exterior.coords]
                    for poligono in multi.geoms
                ]   
            ee_geometry = ee.Geometry.MultiPolygon(multip_list)
            #trovo paesi intersezione
            paesi_contenenti = paesi.filterBounds(ee_geometry)
            nomi_paesi = paesi_contenenti.aggregate_array('ADM0_NAME').getInfo()
            countries[codice]=nomi_paesi

#esportazione
output_path=os.path.join(output_folder, "nazioni.pkl")
with open(output_path, "wb") as f:
    pickle.dump(countries, f)