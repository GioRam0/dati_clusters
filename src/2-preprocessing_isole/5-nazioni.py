#importo librerie
import geopandas as gp
import ee
import os
import sys
import pickle

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")

#importo coordinate isole
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2_arro3.gpkg")
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

#definisco una funzione che prende in input una feature contenente un'isola e aggiunge una colonna con le nazioni che la intersecano
def island_feature(feature):
    geom = feature.geometry()
    intersects = paesi.filterBounds(geom)
    names = intersects.aggregate_array('ADM0_NAME')
    return feature.set({'intersecting_countries': names})

#funzione da applicare a un dataframe e aggiunge al dizionario le liste di paesi intersecanti le isole
def get_gdf_dict(df):
    #lista di features da riempire
    feats = []
    for idx, row in df.iterrows():
        codice= row['ALL_Uniq']
        if codice in countries:
            continue  # skip isola già elaborata
        geojson = row['geometry'].__geo_interface__
        feats.append(
            ee.Feature(ee.Geometry(geojson), {'_idx': idx, 'name': row['ALL_Uniq']})
        )
    #la trasformo in una feature collection e mappo la funzione island_feature
    fc = ee.FeatureCollection(feats)
    result_fc = fc.map(island_feature)
    features = result_fc.getInfo()['features']
    #aggiorno il dizionario
    for f in features:
        name = f['properties']['name']
        country_list = f['properties']['intersecting_countries']
        countries[name] = list(dict.fromkeys(country_list))

#suddivido le isole in base alle dimensioni e suddivido i dataframe in lunghezze diverse per non superare il payload massimo
print(len(gdf))
gdf1=gdf[(gdf['IslandArea']<=500)]
print(len(gdf1))
#applico iterativamente ed esporto periodicamente
imp=50
a=0
b=a+imp
while True:
    if b%200==0 or b==len(gdf1):
        print(b)
    gd=gdf1.iloc[a:b]
    get_gdf_dict(gd)
    #esportazione
    output_path=os.path.join(output_folder, "nazioni.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(countries, f)
    if b==(len(gdf1)):
        break
    else:
        a+=imp
        b+=imp
        b=min(b,(len(gdf1)))
print('isole molto piccole terminate')

gdf1=gdf[(gdf['IslandArea']>500) & (gdf['IslandArea']<=1000)]
print(len(gdf1))
imp=20
a=0
b=a+imp 
while True:
    if b%40==0 or b==len(gdf1):
        print(b)
    gd=gdf1.iloc[a:b]
    get_gdf_dict(gd)
    #esportazione
    output_path=os.path.join(output_folder, "nazioni.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(countries, f)
    if b==(len(gdf1)):
        break
    else:
        a+=imp
        b+=imp
        b=min(b,(len(gdf1)))
print('isole piccole terminate')

gdf1=gdf[(gdf['IslandArea']>1000) & (gdf['IslandArea']<=3000)]
print(len(gdf1))
imp=10
a=0
b=a+imp
while True:
    print(b)
    gd=gdf1.iloc[a:b]
    get_gdf_dict(gd)
    #esportazione
    output_path=os.path.join(output_folder, "nazioni.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(countries, f)
    if b==(len(gdf1)):
        break
    else:
        a+=imp
        b+=imp
        b=min(b,(len(gdf1)))
print('isole medie terminate')

gdf1=gdf[(gdf['IslandArea']>3000) & (gdf['IslandArea']<=5000)]
print(len(gdf1))
imp=4
a=0
b=a+imp 
while True:
    print(b)
    gd=gdf1.iloc[a:b]
    get_gdf_dict(gd)
    #esportazione
    output_path=os.path.join(output_folder, "nazioni.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(countries, f)
    if b==(len(gdf1)):
        break
    else:
        a+=imp
        b+=imp
        b=min(b,(len(gdf1)))
print('isole medio-grandi terminate')

gdf1=gdf[(gdf['IslandArea']>5000) & (gdf['IslandArea']<=10000)]
print(len(gdf1))
imp=3
a=0
b=a+imp 
while True:
    print(b)
    gd=gdf1.iloc[a:b]
    get_gdf_dict(gd)
    #esportazione
    output_path=os.path.join(output_folder, "nazioni.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(countries, f)
    if b==(len(gdf1)):
        break
    else:
        a+=imp
        b+=imp
        b=min(b,(len(gdf1)))
print('isole grandi terminate')

#semplifico la geometria di un'isola molto grande che senza semplificazione supera il payload massimo di google earth
codice=gdf.query("ALL_Uniq == 273766").index[0]
multi=gdf.loc[codice, 'geometry']
multi1=(multi.simplify(tolerance=0.005, preserve_topology=True))
gdf.loc[codice, 'geometry']=multi1
gdf1=gdf[(gdf['IslandArea']>=10000)]
print(len(gdf1))
imp=1
a=0
b=a+imp
while True:
    print(b)
    gd=gdf1.iloc[a:b]
    get_gdf_dict(gd)
    #esportazione
    output_path=os.path.join(output_folder, "nazioni.pkl")
    with open(output_path, "wb") as f:
        pickle.dump(countries, f)
    if b==(len(gdf1)):
        break
    else:
        a+=imp
        b+=imp
        b=min(b,(len(gdf1)))
print('isole molto grandi terminate')