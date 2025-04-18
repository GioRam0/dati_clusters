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

#i=4
#multi=gdf.loc[i,'geometry']
#print(gdf.loc[i,'IslandArea'])
#print(multi.centroid)
#point=ee.Geometry.Point(-49.074993,-1.805626)
#creo i dizionari da riempire
superficie={}
isl_nod={}
ele_max={}
#itero per le isole
for i,isl in gdf.iterrows():
    multi=isl.geometry
    codice=isl.ALL_Uniq
    #area1=isl.IslandArea
    #creo la figuro come ee.Geometry, con cui google lavora
    multip_list =[ 
            [list(vertice) for vertice in poligono.exterior.coords]
            for poligono in multi.geoms
    ]   
    ee_geometry = ee.Geometry.MultiPolygon(multip_list)
    #calcolo l'area di questa figura
    area0=ee_geometry.area().getInfo()

    #dataset delle aree protette, da escludere
    wdpa_polygons = ee.FeatureCollection('WCMC/WDPA/current/polygons')
    #aree che intersecano l'isola
    intersecting_wdpa = wdpa_polygons.filter(ee.Filter.intersects('.geo', ee_geometry))
    union_of_intersecting_wdpa = intersecting_wdpa.union()
    #elimino le aree protette
    ee_geometry = ee_geometry.difference(union_of_intersecting_wdpa)
    #se rimane trppo poco terreno (2 ettari, corrispondo a meno di un MW di fotovoltaico)
    #mi fermo
    if ee_geometry.area().getInfo()<20000:
        superficie[codice]=0
        break
    #importo image sull'elevazione
    ele=ee.Image("USGS/GMTED2010_FULL")
    #ritaglio sull'isola e seleziono la banda opportuna
    ele_clip=ele.clip(ee_geometry).select('mea')
    #creo una maschera con i pixel con elevazione <2000 metri, applico la maschera e ricavo la nuova geometria
    ele_mask=ele_clip.lt(2000).rename('ele_mask')
    ele_image=ele_clip.updateMask(ele_mask)
    ele_geometry=ele_image.geometry()
    ee_geometry=ee_geometry.intersection(ele_geometry, ee.ErrorMargin(10))
    #print(ee_geometry.area().getInfo())
    #calcolo elevazione max
    max_value_dict = ele_clip.reduceRegion(
        reducer=ee.Reducer.max(),
        geometry=ee_geometry,
        scale=ele_clip.projection().nominalScale(),
        bestEffort=True,
        maxPixels=1e9
    )
    max=max_value_dict.getInfo()
    ele_max[codice]=max
    
    #calcolo l'image con la pendenza e creo la maschera con i valori minori di 11.31 gradi (20%)
    slope = ee.Terrain.slope(ele_clip)
    slope_mask=slope.lt(11.31).rename('slope_mask')
    slope_image=slope.updateMask(ele_mask)
    slope_geometry=slope_image.geometry()
    ee_geometry=ee_geometry.intersection(slope_geometry, ee.ErrorMargin(10))
    #print(ee_geometry.area().getInfo())

    #alternativa, cofnronta
    #importo il dataset sull'elevazione
    #ele=ee.ImageCollection("JAXA/ALOS/AW3D30/V3_2")
    #trovo le immagini che intersecano l'isola
    #collection=ele.filterBounds(ee_geometry)
    #se una sola (isola interamente contenuta) creo la maschera e la applico
    #if collection.size().getInfo()==1:
    #    ele_clip=collection.first().clip(ee_geometry).select('DSM')
    #    ele_mask=ele_clip.first().lt(2000).rename('ele_mask')
    #    ele_image=ele_clip.updateMask(ele_mask)
    #    ele_geometry=ele_image.geometry()
    #    ee_geometry=ee_geometry.intersection(ele_geometry, ee.ErrorMargin(10))
    #    max_value_dict = ele_clip.reduceRegion(
    #        reducer=ee.Reducer.max(),
    #        geometry=ee_geometry,
    #        scale=ele_clip.projection().nominalScale(),
    #        bestEffort=True,
    #        maxPixels=1e9
    #    )
    #    max=max_value_dict.getInfo()
    #    ele_max[codice]=max
    #
    #    slope = ee.Terrain.slope(ele_clip)
    #    slope_mask=slope.lt(11.31).rename('ele_mask')
    #    slope_image=slope.updateMask(ele_mask)
    #    slope_geometry=slope_image.geometry()
    #    ee_geometry=ee_geometry.intersection(slope_geometry, ee.ErrorMargin(10))
    #se piu di uno itero per le diverse immagini e calcolo le zone da escludere sottraedole di volta in volta dalla ee_geometry
    #else:
    #    list=collection.toList(collection.size())
    #    max=0
    #    for i in range(collection.size().getInfo()):
    #        band=list.get(i).select('DSM')
    #        ele_mask=band.gt(2000).rename('ele_mask')
    #        ele_image=band.updateMask(ele_mask)
    #        ele_geometry=ele_image.geometry()
    #        ee_geometry=ee_geometry.difference(ele_geometry, ee.ErrorMargin(10))
    #        max_value_dict = ele_clip.reduceRegion(
    #            reducer=ee.Reducer.max(),
    #            geometry=ee_geometry,
    #            scale=ele_clip.projection().nominalScale(),
    #            bestEffort=True,
    #            maxPixels=1e9
    #        )
    #        max1=max_value_dict.getInfo()
    #        if max1>max:
    #            max=max1
    #        slope = ee.Terrain.slope(band)
    #        slope_mask=slope.gt(11.31).rename('ele_mask')
    #        slope_image=slope.updateMask(ele_mask)
    #        slope_geometry=slope_image.geometry()
    #        ee_geometry=ee_geometry.intersection(slope_geometry, ee.ErrorMargin(10))
    #    ele_max[codice]=max
    #print(ee_geometry.area().getInfo())

    #importo dataset sulle caratteristiche del terreno
    lc100_collection = ee.ImageCollection("COPERNICUS/Landcover/100m/Proba-V-C3/Global")
    lc_image = ee.Image(lc100_collection.sort('system:time_start', False).first()).select('discrete_classification')
    #valori corrispondenti ai terreni non agibili
    excluded_values = [0, 40, 50, 70, 80, 90, 111, 112, 113, 114, 115, 116, 200]
    lc_clipped = lc_image.clip(ee_geometry)
    #maschera per i punti senza dati, se troppi raccolgo questa informazione nel dizionario nodata
    lc_mask = lc_clipped.neq(excluded_values[0])

    one_count = lc_mask.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=lc_clipped.geometry(),
        scale=lc_clipped.projection().nominalScale(),
        maxPixels=1e9
    ).get('discrete_classification').getInfo()
    zeros = lc_mask.eq(0)
    zero_count = zeros.reduceRegion(
        reducer=ee.Reducer.sum(),
        geometry=lc_clipped.geometry(),
        scale=lc_clipped.projection().nominalScale(),
        maxPixels=1e9
    ).get('discrete_classification').getInfo()
    if (zero_count/one_count)>0.5:
        isl_nod[codice]=1
    else:
        isl_nod[codice]=0
    
    #itero per gli altri terreni non agibili e applico la maschera
    for i in range(1, len(excluded_values)):
        lc_mask=lc_mask.And(lc_clipped.neq(excluded_values[i]))
    lc_image=lc_clipped.updateMask(lc_mask)
    lc_geometry=lc_image.geometry()
    ee_geometry=ee_geometry.intersection(lc_geometry, ee.ErrorMargin(10))

    #area agibile
    area=ee_geometry.area().getInfo()
    print(area1/area)
    superficie[codice]=(area/area0)*100

#esportazione
percorso_folder_out = os.path.join(cartella_progetto, "data/dati_finali/superficie_res")
os.makedirs(percorso_folder_out, exist_ok=True)
percorso_file=os.path.join(percorso_folder_out, "superficie_res.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(superficie, f)
percorso_file=os.path.join(percorso_folder_out, "superficie_nod.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(isl_nod, f)
percorso_file=os.path.join(percorso_folder_out, "ele_max.pkl")
with open(percorso_file, "wb") as f:
    pickle.dump(ele_max, f)