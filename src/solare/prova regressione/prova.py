#importo le librerie
import rasterio
import rasterio.mask
from shapely.geometry import box, mapping
import numpy as np
import pandas as pd
import pickle
import os
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
nome_file=os.path.join(cartella_corrente, "dataframe.pkl")
gdf = pd.read_pickle(nome_file)

#gdf['lat_band'] = pd.cut(gdf['yc'], bins=[-90, -60, -50, -40, -30, -20, -10, 10, 20, 30, 40, 50, 60, 70, 90])
#lat_band_means = gdf.groupby('lat_band')['solar'].mean()
#lat_band_std = gdf.groupby('lat_band')['solar'].std()
#print(lat_band_means)
#print(lat_band_std)

gdf['temp_band'] = pd.cut(gdf['temp'], bins=[-15, -5, 0, 5, 10, 15, 20, 25, 31])
lat_band_means = gdf.groupby('temp_band')['solar'].mean()
lat_band_std = gdf.groupby('temp_band')['solar'].std()
print(lat_band_means)
print(lat_band_std)

gdf['lat_band'] = pd.cut(gdf['yc'], bins=[-90, -60, -50, -40, -30, -20, -10, 10, 20, 30, 40, 50, 60, 70, 90])
lat_band_means = gdf.groupby('lat_band')['solar'].mean()
lat_band_std = gdf.groupby('lat_band')['solar'].std()
print(lat_band_means)
print(lat_band_std)

#gdf=gdf[(gdf['temp']<20) & (gdf['temp']>31) & (np.isnan(gdf['solar']))]
#print(gdf)
#print(len(gdf))

#un'isola con centro fuori nod[0,1] e pow numerico
#73 isole con centro fuori nod[1,1] e pow nan
#26 isole con centro dentro nod [0,1] e pow nan
#3 isole con centro dentro nod [0,0] e pow nan

#gdf=gdf[(np.isfinite(gdf['solar']))]
#gdf=gdf[(gdf['yc']>40)]
#print(len(gdf))
#
##gdf['phi_rad'] = np.deg2rad(gdf['yc'])
##gdf['cos_phi'] = np.cos(gdf['phi_rad'])
#
#X = gdf[['yc','temp', 'prec']]
#y = gdf['solar'].values
#X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
#
#
##poly = PolynomialFeatures(degree=5, include_bias=True)
##X_poly = poly.fit_transform(gdf[['yc','temp','prec']])
#
##model = LinearRegression().fit(X_poly, y)
#model = RandomForestRegressor(n_estimators=100, random_state=42)
#model.fit(X_train, y_train)
#predictions = model.predict(X_test)
#
#r2 = r2_score(y_test, predictions)
#print(r2)