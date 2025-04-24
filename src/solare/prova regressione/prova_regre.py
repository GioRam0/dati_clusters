#importo le librerie
import rasterio
import rasterio.mask
from shapely.geometry import box, mapping
import numpy as np
import geopandas as gp
import pickle
import os
# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")
percorso_pkl=os.path.join(cartella_corrente, "solar_pow.pkl")
with open(percorso_pkl, 'rb') as file:
        pow = pickle.load(file)
percorso_pkl=os.path.join(cartella_corrente, "nodata.pkl")
with open(percorso_pkl, 'rb') as file:
        nod = pickle.load(file)
percorso_pkl=os.path.join(cartella_corrente, "prec.pkl")
with open(percorso_pkl, 'rb') as file:
        prec = pickle.load(file)
percorso_pkl=os.path.join(cartella_corrente, "isl_nodp.pkl")
with open(percorso_pkl, 'rb') as file:
        prec_nodata = pickle.load(file)
percorso_pkl=os.path.join(cartella_corrente, "temp.pkl")
with open(percorso_pkl, 'rb') as file:
        temp = pickle.load(file)
percorso_pkl=os.path.join(cartella_corrente, "isl_nodt.pkl")
with open(percorso_pkl, 'rb') as file:
        temp_nodata = pickle.load(file)
#importo dati isole
percorso_file=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate_tot.gpkg")
gdf = gp.read_file(percorso_file)
gdf=gdf[(gdf['IslandArea']<10000)]

gdf['yc']=float(0)
gdf['solar']=float(0)
gdf['snod']=[[0,0] for _ in range(len(gdf))]
gdf['temp']=float(0)
gdf['tnod']=float(0)
gdf['prec']=float(0)
gdf['pnod']=float(0)
print(len(gdf))

k=0
for i,isl in gdf.iterrows():
        if k%100==0:
                print(k)
        k+=1
        multi=isl.geometry
        codice=isl.ALL_Uniq
        gdf.loc[i,'yc']=multi.centroid.y
        gdf.loc[i,'solar']=pow[codice]
        gdf.loc[i,'snod'][0]=nod[codice][0]
        gdf.loc[i,'snod'][1]=nod[codice][1]
        gdf.loc[i,'temp']=temp[codice]
        gdf.loc[i,'tnod']=temp_nodata[codice]
        gdf.loc[i,'prec']=prec[codice]
        gdf.loc[i,'pnod']=prec_nodata[codice]

gdf=gdf[['yc','solar','snod', 'temp', 'tnod', 'prec', 'pnod']]
percorso_out = os.path.join(cartella_corrente, "dataframe.pkl")
gdf.to_pickle(percorso_out)