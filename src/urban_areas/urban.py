#importo librerie
import geopandas as gp
import ee
import pickle
import os
import sys

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")

#importo coordinate isole
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2.gpkg")
gdf = gp.read_file(isl_path)

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo la variabile project
import config
proj = config.proj
ee.Initialize(project=proj)

#importo il dataset e seleziono l'ultima immagine presente, non futura
urban_collection=ee.ImageCollection("JRC/GHSL/P2023A/GHS_SMOD_V2-0")
filtered_collection=urban_collection.filterDate('2000-01-01', '2025-01-01')
sorted_collection=filtered_collection.sort('system:time_start', False)
urban_image=ee.Image(sorted_collection.first())
#valori dei pixel urbani
urban_values = [30, 23, 22]
image_start = ee.Date(urban_image.get('system:time_start'))
print(image_start.get('year').getInfo())
#image_end = ee.Date(urban_image.get('system:time_start'))
#print(image_end.get('year').getInfo())

#se gia presenti (effettuata una precedente run ma interrotta) importo i dati precedentemente scaricati per non ricominciare
output_folder = os.path.join(cartella_progetto, "data/dati_finali/urban")
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, "urban.pkl")
if os.path.exists(output_path):
    with open(output_path, 'rb') as file:
        urban = pickle.load(file)
    output_path = os.path.join(cartella_corrente, "urban_rel.pkl")
    with open(output_path ,  'rb') as file:
            urban_rel = pickle.load(file)
#se non presenti inizializzo i dizionari
else:
    urban={}
    urban_rel={}

#itero per le isole
k=0
for i,isl in gdf.iterrows():
    k=0
for i,isl in gdf.iterrows():
    if k % 200 == 0:
        #esportazione periodica per non dover riiniziare da capo in caso di interruzione
        print(k)
        output_path=os.path.join(output_folder, "urban.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(urban, f)
        output_path=os.path.join(output_folder, "urban_nodata.pkl")
        with open(output_path, "wb") as f:
            pickle.dump(urban_rel, f)
    k+=1
    codice=isl.ALL_Uniq
    if codice not in urban:
        multi=isl.geometry
        multip_list =[ 
                [list(vertice) for vertice in poligono.exterior.coords]
                for poligono in multi.geoms
            ]   
        ee_geometry = ee.Geometry.MultiPolygon(multip_list)
        #calcolo l'area di questa figura
        area0=ee_geometry.area().getInfo()    
        #creo una maschera con i pixel urbani e la applico all'immagine ritagliata alla forma dell'isola
        clipped_image = urban_image.clip(ee_geometry)
        urban_mask = clipped_image.eq(urban_values[0])
        urban_mask = urban_mask.Or(clipped_image.eq(urban_values[1]))
        urban_mask = urban_mask.Or(clipped_image.eq(urban_values[2]))
        urban_image=clipped_image.updateMask(urban_mask)
        #estraggo la geometria risultante e ne calcolo la superficie
        urban_geometry=urban_image.geometry()
        #calcolo l'area urbana da questa figura
        urban_area = urban_geometry.area().getInfo()
        #faccio il rapporto e lo rendo percentuale
        urban_relative=(urban_area/area0)*100
        #la trasformo in km2
        urban_area=urban_area/1000000
        urban[codice]=urban_area
        urban_rel[codice]=urban_relative

#esportazione
output_path=os.path.join(output_folder, "urban_area.pkl")
with open(output_path, "wb") as f:
    pickle.dump(urban, f)
output_path=os.path.join(output_folder, "urban_area_rel.pkl")
with open(output_path, "wb") as f:
    pickle.dump(urban_rel, f)