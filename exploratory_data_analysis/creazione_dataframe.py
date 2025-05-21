#importo le librerie
import geopandas as gp
import numpy as np
import pickle
import os

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..")

#importo le isole ed elimino la colonna geometrica
isl_path=os.path.join(cartella_progetto, "data/isole_filtrate", "isole_filtrate2_arro4.gpkg")
gdf = gp.read_file(isl_path)
df = gdf.drop(columns=['geometry'])
del gdf

#importo i vari dizionari pkl contenenti i dati tramite una funzione
pkl_folder=os.path.join(cartella_progetto, "data/dati_finali")

def create_dict(str):
    if str=='gdp_nodata':
        nome=str[0:4]+'isola_non_completa'
        df[nome]=float(0)
    if str=='solar_nodata':
        nome=str[0:6]+'isola_non_completa'
        df[nome]=float(0)
    df[str]=float(0)
    nome=str+'.pkl'
    percorso_pkl=os.path.join(pkl_folder1, nome)
    with open(percorso_pkl, 'rb') as file:
        return pickle.load(file)
    
pkl_folder1=os.path.join(pkl_folder, "biomassa")
evi=create_dict('evi')
evi_nodata=create_dict("evi_nodata")

pkl_folder1=os.path.join(pkl_folder, "eolico")
eolico = create_dict("eolico")
eolico_nodata=create_dict("eolico_nodata")
eolico_std=create_dict("eolico_std")
offshore=create_dict("offshore")

pkl_folder1=os.path.join(pkl_folder, "gdp")
gdp=create_dict("gdp")
gdp_nodata=create_dict("gdp_nodata")
gdp_procapite=create_dict("gdp_pro_capite")

pkl_folder1=os.path.join(pkl_folder, "geotermico")
geothermal_potential=create_dict("geothermal_potential")

pkl_folder1=os.path.join(pkl_folder, "hydro")
hydro=create_dict("hydro")

pkl_folder1=os.path.join(pkl_folder, "metereologici")
temp=create_dict("temp")
temp_nodata=create_dict("temp_nodata")
prec=create_dict("prec")
prec_nodata=create_dict("prec_nodata")
hdd=create_dict("hdd")
hdd_nodata=create_dict("hdd_nodata")
cdd=create_dict("cdd")
cdd_nodata=create_dict("cdd_nodata")

pkl_folder1=os.path.join(pkl_folder, "solare")
solar_pow= create_dict("solar_pow")
solar_std= create_dict("solar_std")
solar_nodata= create_dict("solar_nodata")

pkl_folder1=os.path.join(pkl_folder, "urban")
urban_area=create_dict("urban_area")
urban_area_rel=create_dict("urban_area_rel")

pkl_folder1=os.path.join(pkl_folder, "superficie_res")
superficie_res=create_dict("superficie_res")
ele_max=create_dict("ele_max")

#creo un dizionario che per ogni colonna nodata valuta conta le righe in cui il booleano non corrisponde con dato isnan 
diz={}
diz['evi']=[0,0]
diz['eolico']=[0,0]
diz['gdp']=[0,0]
diz['temp']=[0,0]
diz['prec']=[0,0]
diz['hdd']=[0,0]
diz['cdd']=[0,0]
diz['solar']=[0,0]
gdp_non_complete=0
solar_non_complete=0
#riempio le nuove colonne del dataframe
for i,isl in df.iterrows():
    codice=isl.ALL_Uniq
    df.loc[i,'evi']=evi[codice]
    df.loc[i,'evi_nodata']=evi_nodata[codice]
    if np.isnan(evi[codice]) and evi_nodata[codice]==0:
        diz['evi'][0]+=1
    if (not np.isnan(evi[codice])) and evi_nodata[codice]==1:
        diz['evi'][1]+=1
    df.loc[i,'eolico']=eolico[codice]
    df.loc[i,'eolico_nodata']=eolico_nodata[codice]
    if np.isnan(eolico[codice]) and eolico_nodata[codice]==0:
        diz['eolico'][0]+=1
    if (not np.isnan(eolico[codice])) and eolico_nodata[codice]==1:
        diz['eolico'][1]+=1
    df.loc[i,'eolico_std']=eolico_std[codice]
    df.loc[i,'offshore']=offshore[codice]
    df.loc[i,'gdp']=gdp[codice]
    df.loc[i,'gdp_procapite']=gdp_procapite[codice]
    df.loc[i,'gdp_nodata']=gdp_nodata[codice][0]
    if np.isnan(gdp[codice]) and gdp_nodata[codice][0]==0:
        diz['gdp'][0]+=1
    if (not np.isnan(gdp[codice])) and gdp_nodata[codice][0]==1:
        diz['gdp'][1]=1
    df.loc[i,'gdp_isola_non_completa']=gdp_nodata[codice][1]
    if gdp_nodata[codice][1]==1:
        gdp_non_complete+=1
    df.loc[i,'geothermal_potential']=geothermal_potential[codice]
    df.loc[i,'hydro']=hydro[codice]
    df.loc[i,'temp']=temp[codice]
    df.loc[i,'temp_nodata']=temp[codice]
    if np.isnan(temp[codice]) and temp_nodata[codice]==0:
        diz['temp'][0]+=1
    if (not np.isnan(temp[codice])) and temp_nodata[codice]==1:
        diz['temp'][1]+=1
    df.loc[i,'prec']=prec[codice]
    df.loc[i,'prec_nodata']=prec_nodata[codice]
    if np.isnan(prec[codice]) and prec_nodata[codice]==0:
        diz['prec'][0]+=1
    if (not np.isnan(prec[codice])) and prec_nodata[codice]==1:
        diz['prec'][1]+=1
    df.loc[i,'hdd']=hdd[codice]
    df.loc[i,'hdd_nodata']=hdd_nodata[codice]
    if np.isnan(hdd[codice]) and hdd_nodata[codice]==0:
        diz['hdd'][0]+=1
    if (not np.isnan(hdd[codice])) and hdd_nodata[codice]==1:
        diz['hdd'][1]+=1
    df.loc[i,'cdd']=cdd[codice]
    df.loc[i,'cdd_nodata']=cdd_nodata[codice]
    if np.isnan(cdd[codice]) and cdd_nodata[codice]==0:
        diz['cdd'][0]+=1
    if (not np.isnan(cdd[codice])) and cdd_nodata[codice]==1:
        diz['cdd'][1]+=1
    df.loc[i,'solar_pow']=solar_pow[codice]
    df.loc[i,'solar_std']=solar_std[codice]
    df.loc[i,'solar_nodata']=solar_nodata[codice][0]
    if np.isnan(solar_pow[codice]) and solar_nodata[codice][0]==0:
        diz['solar'][0]+=1
    if (not np.isnan(solar_pow[codice])) and solar_nodata[codice][0]==1:
        diz['solar'][1]+=1
    df.loc[i,'solar_isola_non_completa']=solar_nodata[codice][1]
    if solar_nodata[codice][1]==1:
        solar_non_complete+=1
    df.loc[i,'urban_area']=urban_area[codice]
    df.loc[i,'urban_area_rel']=urban_area_rel[codice]
    df.loc[i,'superficie_res']=superficie_res[codice]
    df.loc[i,'ele_max']=ele_max[codice]
#droppo le colonne nodata e elimino le righe con dati incompleti, una volta fatta l'analisi posso anche non importarle proprio
print(diz)
print(f'le isole non completamente coperte dal file sul solare sono {solar_non_complete}')
print(f'le isole non completamente coperte dal file sul gdp sono {gdp_non_complete}')

df = df.drop(columns=['evi_nodata', 'eolico_nodata', 'gdp_nodata', 'gdp_isola_non_completa', 'temp_nodata', 'prec_nodata', 'hdd_nodata', 'cdd_nodata', 'solar_nodata', 'solar_isola_non_completa'])
df=df.drop(columns=['Shape_Leng'])

print(f"tutte le isole sono {len(df)}")
df=df.dropna()
print(f"le isole con dati completi sono {len(df)}")

def etichettatura(valore, soglie, etichette):
    if valore < soglie[0]:
        return etichette[0]
    for i in range(len(soglie) - 1):
        if soglie[i] <= valore < soglie[i+1]:
            return etichette[i+1]
    if valore >= soglie[-1]:
        return etichette[-1]

soglie_den=[50,350]
soglie_solar=[3.5,4.5]
soglie_gdp=[1036, 4045, 12535]
etichette=['XS','S','M','L']
df['Densità_pop_etichetta']=df['Densità_pop'].apply(etichettatura, args=(soglie_den, etichette[1:]))
for etic in etichette[1:]:
    len=len(gdf(gdf['Densità_pop_etichetta']==etic))
    print(f'Ci sono {len} isole con etichetta {etic} per la densità abitativa')
df['Solar_etichetta']=df['Solar_pow'].apply(etichettatura, args=(soglie_solar, etichette[1:]))
for etic in etichette[1:]:
    len=len(gdf(gdf['Solar_etichetta']==etic))
    print(f'Ci sono {len} isole con etichetta {etic} per la potenza solare')
df['GDP_pc_etichetta']=df['gdp_procapite'].apply(etichettatura, args=(soglie_gdp, etichette))
for etic in etichette:
    len=len(gdf(gdf['GDP_pc_etichetta']==etic))
    print(f'Ci sono {len} isole con etichetta {etic} per il GDP pro capite')
soglie_wind_power=[100, 150, 200, 250, 300, 400]
wind_classes=[1,2,3,4,5,6,7]
soglie_wind_cubo=nuova_lista = [elemento / 1.225 for elemento in soglie_wind_power]
df['Wind_class']=df['eolico'].apply(etichettatura, args=(soglie_wind_cubo, wind_classes))
for classe in wind_classes:
    len=len(gdf(gdf['Wind_class']==classe))
    print(f'Ci sono {len} isole con classe di vento {classe}')
df['NO_res'] = np.where(df['superficie_res'] == 0, 1, 0)
len=len(gdf(gdf['NO_res']==1))
print(f'Ci sono {len} isole con senza superficie agibile per rinnovabili')

output_folder = os.path.join(cartella_corrente, 'risultati')
os.makedirs(output_folder, exist_ok=True)
output_path = os.path.join(output_folder, 'analisys_df.pkl')
df.to_pickle(output_path)