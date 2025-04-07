#importo le librerie
import atlite
import geopandas as gpd
import xarray as xr
import rioxarray
from shapely.geometry import Polygon
import os
import sys

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..")
# percorso file config
percorso_config = os.path.join(cartella_corrente, "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo le variabili config
import config
start_date=config.START_DATE
end_date=config.END_DATE

#importo dati isole
#adesso prova
isl_file = os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2_arro2.gpkg")
gdf = gpd.read_file(isl_file)
gdf=gdf=gdf[(gdf['IslandArea']>900)]
multi=gdf.iloc[0]["geometry"]
#lista perche il clip richiede un oggetto iterabile in input (lista di poligoni)
list=[]
for poli in multi.geoms:
    list.append(poli)
xmin,ymin,xmax,ymax=multi.bounds
####CHIARIRE BOUNDS TROPPO VICINI
xmin-=2
xmax+=2
ymin-=2
ymax+=2
####CHIARIRE ERA5-LAND
####CHIARIRE ISOLA PICCOLA

# creazione del cutout con dati ERA5
cutout = atlite.Cutout(
    path="era5_wind_data.nc",  # Nome del file di output
    module="era5",             # Dati da ERA5
    x=slice(xmin, xmax),        # Estensione longitudinale
    y=slice(ymin, ymax),        # Estensione latitudinale
    time=slice(start_date, end_date),  # Periodo
    dx=0.25,  # Risoluzione spaziale (~31 km)
    dy=0.25
)
cutout.prepare(features=["wind"])
####CHIARIRE CON ALTRE TURBINE, unita misura MW potenza output, potrei fare MWout/MWnom
####CHIARIRE DENSITA DELL'ARIA, POTREI MOLTIPLICARE TUTTO PER PRESSIONE E TEMPE TANTO SONO DIRETTAMENTE PROPORZIONALI
wind_power = cutout.wind(turbine="Vestas_V90_3MW")
###UN SOLO ISTANTE TEMPORALE NON FACCIO MEDIA, DA CHIARIRE

##per considerare i singoli mesi dovrei fare cosi
#wind_power_gen = wind_power.sel(time=ds.time.dt.month == 1)

#clipping nel poligono
wind_power.rio.set_spatial_dims(x_dim="x", y_dim="y")
wind_power.rio.write_crs("EPSG:4326", inplace=True)
clipped_wind_power = wind_power.rio.clip(list, gdf.crs, drop=True)
#velocità del vento all'interno del poligono
average_wind_power = clipped_wind_power.mean().compute().item()

#def mean_p(multi):
#
#    return power
#
#def var_p(multi):
#
#    return variance
#
#wind_power={}
#wind_power_var={}
#k=0
#for ind,isl in gdf.iterrows():
#    if k%100==0:
#        print(k)
#    k+=1
#    codice=isl.ALL_Uniq
#    multi=isl.geometry
#    mean=mean_p(multi)
#    var=var_p(multi)
#    wind_power[codice]=mean
#    wind_power_var=var
