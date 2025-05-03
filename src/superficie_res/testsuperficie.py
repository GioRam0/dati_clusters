#importo librerie
import geopandas as gp
import ee
import os
import sys
import geemap
from shapely import Polygon

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")

#importo coordinate isole
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2_arro3.gpkg")
gdf = gp.read_file(isl_path)
gdf=gdf.iloc[0:40]

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo la variabile project
import config
proj = config.proj
ee.Initialize(project=proj)

output_folder = os.path.join(cartella_progetto, "data/dati_finali/superficie_res/visualizzazione")
os.makedirs(output_folder, exist_ok=True)

#itero per le isole
for k, (i, isl) in enumerate(gdf.iterrows(), 1):
    print(k)
    #geometeria dell'isola e conversione in ee.geometry
    geometria=isl.geometry.simplify(tolerance=0.005, preserve_topology=True)
    if isinstance(geometria, Polygon):
        vertici_list = [vertice for vertice in geometria.exterior.coords]
        ee_geometry_original = ee.Geometry.Polygon(vertici_list)
    else:
        multip_list = [
            [vertice for vertice in poligono.exterior.coords]
            for poligono in geometria.geoms
        ]
        ee_geometry_original = ee.Geometry.MultiPolygon(multip_list)
    #calcolo l'area di questa figura
    area0=ee_geometry_original.area().getInfo()
    print(area0)
    #creo la mappa e aggiungo il layer dell'isola originale
    m = geemap.Map()
    m.add_layer(ee_geometry_original, {'color': 'green'}, f'Isola originale')
    m.centerObject(ee_geometry_original,zoom=10)
    output_path = os.path.join(output_folder, f"mappa_interattiva{k}.html")
    m.to_html(output_path)
    #dataset delle aree protette, da escludere
    wdpa_polygons = ee.FeatureCollection('WCMC/WDPA/current/polygons')
    #aree che intersecano l'isola
    intersecting_wdpa = wdpa_polygons.filter(ee.Filter.intersects('.geo', ee_geometry_original))
    union_of_intersecting_wdpa = intersecting_wdpa.union()
    #elimino le aree protette
    ee_geometry_protected = ee_geometry_original.difference(union_of_intersecting_wdpa)
    area1=ee_geometry_protected.area().getInfo()
    print(area1)
    #aggiungo il layer della nuova geometria
    m.add_layer(ee_geometry_protected, {'color': 'blue'}, f'Isola protected')
    m.centerObject(ee_geometry_original,zoom=10)
    output_path = os.path.join(output_folder, f"mappa_interattiva{k}.html")
    m.to_html(output_path)
    if area1>0:
        #primo dataset altitudine
        ele=ee.Image("USGS/GMTED2010_FULL")
        #clippo l'immagine creo la maschera ed estraggo le geometrie della maschera
        ele_clip=ele.clip(ee_geometry_protected)
        ele_mask=ele_clip.select('mea').lt(2000)
        scale = ele_clip.select('mea').projection().nominalScale().getInfo()
        vectors = ele_mask.selfMask().reduceToVectors(
            geometry=ele_mask.geometry(),
            scale=scale,
            crs=ele_mask.projection().crs(),
            eightConnected=True,
            bestEffort=True
        )
        #unisco le geometrie e le interseco alla geometria precedente
        ele_geometry=vectors.union(ee.ErrorMargin(1)).geometry()
        ee_geometry_alt=ee_geometry_protected.intersection(ele_geometry, ee.ErrorMargin(1))
        area2=ee_geometry_alt.area().getInfo()
        print(area2)
        #aggiungo il layer della nuova geometria
        m.add_layer(ee_geometry_alt, {'color': 'red'}, f'Isola altitudine')

        #secondo dataset altitudine per confronto
        ele1=ee.ImageCollection("JAXA/ALOS/AW3D30/V3_2")
        #trovo le immagini che intersecano l'isola
        collection=ele1.filterBounds(ee_geometry_protected)
        #se una sola (isola interamente contenuta) stesso procedimento di prima
        if collection.size().getInfo()==1:
            ele_clip1=collection.first().clip(ee_geometry_protected)
            ele_mask1=ele_clip1.select('DSM').lt(2000)
            scale = ele_clip1.select('DSM').projection().nominalScale().getInfo()
            vectors = ele_mask1.selfMask().reduceToVectors(
                geometry=ele_mask1.geometry(),
                scale=scale,
                crs=ele_mask1.projection().crs(),
                eightConnected=True,
                bestEffort=True
            )
            ele_geometry1=vectors.union(ee.ErrorMargin(1)).geometry()
            ee_geometry_alt1=ee_geometry_protected.intersection(ele_geometry1, ee.ErrorMargin(1))
        #se piu di uno itero per le diverse immagini e calcolo le zone da escludere sottraedole di volta in volta dalla ee_geometry
        else:
            list=collection.toList(collection.size())
            for j in range(collection.size().getInfo()):
                band=ee.Image(list.get(j)).clip(ee_geometry_protected)
                mask = band.select('DSM').gt(2000)
                scale = band.select('DSM').projection().nominalScale().getInfo()
                vectors = mask.selfMask().reduceToVectors(
                    geometry=mask.geometry(),
                    scale=scale,
                    crs=mask.projection().crs(),
                    eightConnected=True,
                    bestEffort=True
                )
                ele_geometry1=vectors.union(ee.ErrorMargin(1)).geometry()
                if j==0:
                    ee_geometry_alt1=ee_geometry_protected.difference(ele_geometry1, ee.ErrorMargin(1))
                else:
                    ee_geometry_alt1=ee_geometry_alt1.difference(ele_geometry1, ee.ErrorMargin(1))
        area3=ee_geometry_alt1.area().getInfo()
        print(area3)
        #aggiungo il layer alla mappa
        m.add_layer(ee_geometry_alt1, {'color': 'yellow'}, f'Isola altitudine1')
        if area3>0:
            #importo dataset sulle caratteristiche del terreno e seleziono l'immagine piu recente
            lc100_collection = ee.ImageCollection("COPERNICUS/Landcover/100m/Proba-V-C3/Global")
            lc_image = ee.Image(lc100_collection.sort('system:time_start', False).first())
            #valori corrispondenti ai terreni non agibili
            excluded_values = [0, 40, 50, 70, 80, 90, 111, 112, 113, 114, 115, 116, 200]
            lc_clipped = lc_image.clip(ee_geometry_alt1)
            #maschera per i punti senza dati, se troppi raccolgo questa informazione nel dizionario nodata
            lc_mask = lc_clipped.select('discrete_classification').neq(excluded_values[0])        
            #itero per gli altri terreni non agibili e applico la maschera
            for j in range(1, len(excluded_values)):
                lc_mask=lc_mask.And(lc_clipped.select('discrete_classification').neq(excluded_values[j]))
            scale = lc_mask.select('discrete_classification').projection().nominalScale().getInfo()
            vectors = lc_mask.selfMask().reduceToVectors(
                geometry=lc_mask.geometry(),
                scale=scale,
                crs=lc_mask.projection().crs(),
                eightConnected=True,
                bestEffort=True
            )
            lc_geometry=vectors.union(ee.ErrorMargin(1)).geometry()
            ee_geometry_final=ee_geometry_alt1.intersection(lc_geometry, ee.ErrorMargin(1))
            area4=ee_geometry_final.area().getInfo()
            print(area4)
            m.add_layer(ee_geometry_final, {'color': 'pink'}, f'Isola finale')

    #imposto la mappa e la esporto
    m.centerObject(ee_geometry_original,zoom=10)
    output_path = os.path.join(output_folder, f"mappa_interattiva{k}.html")
    m.to_html(output_path)