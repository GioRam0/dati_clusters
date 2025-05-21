import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import scipy.stats as stats

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..")
#importo il dataframe
ris_folder = os.path.join(cartella_corrente, "risultati")
os.makedirs(ris_folder, exist_ok=True)
pkl_path=os.path.join(ris_folder, 'analisys_df.pkl')
df = pd.read_pickle(pkl_path)

output=os.path.join(cartella_corrente,"analisi_dimensioni")
os.makedirs(output, exist_ok=True)
output_folder=os.path.join(output, 'qqplot')
out_folder_raw=[os.path.join(output_folder,"raw")]
os.makedirs(out_folder_raw[0], exist_ok=True)
out_folder_norm_z=[os.path.join(output_folder,"norm_z")]
os.makedirs(out_folder_norm_z[0], exist_ok=True)
out_folder_norm_max=[os.path.join(output_folder,"norm_max")]
os.makedirs(out_folder_norm_max[0], exist_ok=True)

output_folder=os.path.join(output, 'lorenz')
out_folder_raw.append(os.path.join(output_folder,"raw"))
os.makedirs(out_folder_raw[1], exist_ok=True)
out_folder_norm_z.append(os.path.join(output_folder,"norm_z"))
os.makedirs(out_folder_norm_z[1], exist_ok=True)
out_folder_norm_max.append(os.path.join(output_folder,"norm_max"))
os.makedirs(out_folder_norm_max[1], exist_ok=True)

def grafico(col, i, folder):
    plt.figure(figsize=(20, 30))
    stats.probplot(col, dist="norm", plot=plt)
    plt.title(f'QQplot di {i}')
    path=os.path.join(folder[0], f'qqplot_{i}.png')
    plt.savefig(path)
    plt.close()
    if col.min()>=0:
        col1=np.sort(col)
        n=col1.size
        x = np.linspace(0, 1, n)
        cumulative = np.cumsum(col1) / col1.sum()
        cumulative = np.insert(cumulative, 0, 0)
        x = np.insert(x, 0, 0)
        plt.figure(figsize=(20, 30))
        plt.scatter(x, cumulative)
        plt.title(f'Lorenz di {i}')
        plt.grid(True)
        path=os.path.join(folder[1], f'lorenz_{i}.png')
        plt.savefig(path)
        plt.close()

lista=['Popolazione','gdp','nightlights']

#creo i vari qplot
for i in lista:
    colonna = df[i]
    min_val = colonna.min()
    max_val = colonna.max()
    mean_val = colonna.mean()
    std_val = colonna.std()

    #qplot normale
    grafico(colonna, i, out_folder_raw)
    #qplot znormalizzato
    df[f'{i}_z_norm']=(df[i]- mean_val) / std_val
    colonna1 = df[f'{i}_z_norm']
    grafico(colonna1, i, out_folder_norm_z)

    #qplot minmaxnormalizzato
    df[f'{i}_max_norm'] = (df[i] - min_val) / (max_val - min_val)
    colonna1 = df[f'{i}_max_norm']
    grafico(colonna1, i, out_folder_norm_max)
    
    #stessi qplot ma senza outliers
    colonna = df[(df[i]>0)][i]
    Q1 = colonna.quantile(0.25)
    Q3 = colonna.quantile(0.75)
    IQR = Q3 - Q1
    colonna = colonna[(colonna >= Q1 - 1.5 * IQR) & (colonna <= Q3 + 1.5 * IQR)]
    min_val = colonna.min()
    max_val = colonna.max()
    mean_val = colonna.mean()
    std_val = colonna.std()

    #qplot normale
    grafico(colonna, f'{i}_no_outliers', out_folder_raw)
    
    #qplot znormalizzato
    colonna1 = (colonna - mean_val) / std_val
    grafico(colonna1, f'{i}_no_outliers', out_folder_norm_z)

    #qplot minmaxnormalizzato
    colonna1 = (colonna - min_val) / (max_val - min_val)
    grafico(colonna1, f'{i}_no_outliers', out_folder_norm_max)

#unisco popolazione e gdp znormalizzati esporto qqplot normale e senza outliers
df['pop_gdp_z_norm']=(df['Popolazione_z_norm']+df['gdp_z_norm'])/2
colonna=df['pop_gdp_z_norm']
grafico(colonna, f'pop_gdp', out_folder_norm_z)
Q1 = colonna.quantile(0.25)
Q3 = colonna.quantile(0.75)
IQR = Q3 - Q1
colonna = colonna[(colonna >= Q1 - 1.5 * IQR) & (colonna <= Q3 + 1.5 * IQR)]
grafico(colonna, f'pop_gdp_no_outliers', out_folder_norm_z)
#unisco popolazione e gdp maxnormalizzati esporto qqplot normale e senza outliers
df['pop_gdp_max_norm']=(df['Popolazione_max_norm']+df['gdp_max_norm'])/2
colonna=df['pop_gdp_max_norm']
grafico(colonna, f'pop_gdp', out_folder_norm_max)
Q1 = colonna.quantile(0.25)
Q3 = colonna.quantile(0.75)
IQR = Q3 - Q1
colonna = colonna[(colonna >= Q1 - 1.5 * IQR) & (colonna <= Q3 + 1.5 * IQR)]
grafico(colonna, f'pop_gdp_no_outliers', out_folder_norm_max)

#unisco popolazione e nightlights znormalizzati esporto qqplot normale e senza outliers
df['pop_nl_z_norm']=(df['Popolazione_z_norm']+df['nightlights_z_norm'])/2
colonna=df['pop_nl_z_norm']
grafico(colonna, f'pop_nl', out_folder_norm_z)
Q1 = colonna.quantile(0.25)
Q3 = colonna.quantile(0.75)
IQR = Q3 - Q1
colonna = colonna[(colonna >= Q1 - 1.5 * IQR) & (colonna <= Q3 + 1.5 * IQR)]
grafico(colonna, f'pop_nl_no_outliers', out_folder_norm_z)
#unisco popolazione e nightlights maxnormalizzati esporto qqplot normale e senza outliers
df['pop_nl_max_norm']=(df['Popolazione_max_norm']+df['nightlights_max_norm'])/2
colonna=df['pop_nl_max_norm']
grafico(colonna, f'pop_nl', out_folder_norm_max)
Q1 = colonna.quantile(0.25)
Q3 = colonna.quantile(0.75)
IQR = Q3 - Q1
colonna = colonna[(colonna >= Q1 - 1.5 * IQR) & (colonna <= Q3 + 1.5 * IQR)]
grafico(colonna, f'pop_nl_no_outliers.png', out_folder_norm_max)