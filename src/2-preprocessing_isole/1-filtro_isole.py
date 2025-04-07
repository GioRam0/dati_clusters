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
print(len(gdf))

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo le variabili config
import config
min_surface = config.MIN_SUPERFICIE
max_surface = config.MAX_SUPERFICIE

#filtro le isole in base alla superficie
gdf=gdf[(gdf['IslandArea']>=min_surface) & (gdf['IslandArea']<=max_surface)]
print(len(gdf))
#elimino le colonne non rilevanti
gdf=gdf[['ALL_Uniq', 'Name_USGSO', 'Shape_Leng', 'IslandArea', 'geometry']]

#esportazione gpkg
percorso_folder_out = os.path.join(cartella_progetto, "data/isole_filtrate")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_out=os.path.join(percorso_folder_out, "isole_filtrate.gpkg")
gdf.to_file(percorso_out, driver="GPKG")