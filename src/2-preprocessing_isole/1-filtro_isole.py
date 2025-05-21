#importo le librerie
import geopandas as gp
import os
import sys

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto= os.path.join(cartella_corrente, "..", "..")

# percorso completo per il file .gpkg
percorso_file = os.path.join(cartella_progetto, "files", "isole_4326.gpkg")
gdf = gp.read_file(percorso_file)
print(f'lunghezza file: {len(gdf)}')

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo le variabili config
import config
min_surface = config.MIN_SUPERFICIE
max_surface = config.MAX_SUPERFICIE

#filtro le isole in base alla superficie
gdf_big_islands = gdf[(gdf['IslandArea']>max_surface)]
print(f'le isole grandi escluse sono {len(gdf_big_islands)}')
gdf=gdf[(gdf['IslandArea']>=min_surface) & (gdf['IslandArea']<=max_surface)]
print(f'le isole dopo il filtro sono {len(gdf)}')
#elimino le colonne non rilevanti
gdf=gdf[['ALL_Uniq', 'Name_USGSO', 'Shape_Leng', 'IslandArea', 'geometry']]
gdf_big_islands=gdf_big_islands[['ALL_Uniq', 'Name_USGSO', 'Shape_Leng', 'IslandArea', 'geometry']]

#esportazione gpkg
percorso_folder_out = os.path.join(cartella_progetto, "data/isole_filtrate/filtro_superficie")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_out=os.path.join(percorso_folder_out, "isole.gpkg")
gdf.to_file(percorso_out, driver="GPKG")

percorso_folder_out = os.path.join(cartella_progetto, "data/isole_escluse")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_out=os.path.join(percorso_folder_out, "isole_grandi.gpkg")
gdf_big_islands.to_file(percorso_out, driver="GPKG")