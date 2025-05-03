import numpy as np
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..")

#importo il dataframe
ris_folder = os.path.join(cartella_corrente, "risultati")
pkl_path=os.path.join(ris_folder, 'analisys_df.pkl')
df = pd.read_pickle(pkl_path)
colonne_da_escludere = ['ALL_Uniq', 'Shape_Leng']
colonne_da_includere = [col for col in df.columns if col not in colonne_da_escludere]
#dataframe con statistiche descrittive delle varie colonne
descr=df[colonne_da_includere].select_dtypes(include='number').describe()

#calcolo quantili e outlier per ogni colonna, li conto e aggiungo il conteggio al dataframe descrittivo
Q1 = df[colonne_da_includere].select_dtypes(include='number').quantile(0.25)
Q3 = df[colonne_da_includere].select_dtypes(include='number').quantile(0.75)
IQR = Q3 - Q1
is_outlier = ((df[colonne_da_includere].select_dtypes(include='number') < (Q1 - 1.5 * IQR)) | (df[colonne_da_includere].select_dtypes(include='number') > (Q3 + 1.5 * IQR)))
outlier_count = is_outlier.sum()
descr.loc['outliers'] = outlier_count
##esporto il dataframe descrittivo
#output_path=os.path.join(ris_folder, 'statistiche_descrittive.xlsx')
#descr.to_excel(output_path)
##creo ed esporto gli istogrammi
#output_folder = os.path.join(ris_folder, "istogrammi")
#os.makedirs(output_folder, exist_ok=True)
#for col in df[colonne_da_includere].select_dtypes(include='number').columns:
#    output_folder1 = os.path.join(output_folder, "normali")
#    os.makedirs(output_folder1, exist_ok=True)
#    output_path = os.path.join(output_folder1, f"{col}_istogramma.png")
#    plt.figure(figsize=(10, 15))
#    df[col].hist(bins=30, color='skyblue', edgecolor='black')
#    plt.title(f"Istogramma di {col}")
#    plt.xlabel(col)
#    plt.ylabel("Frequenza")
#    plt.tight_layout()
#    plt.savefig(output_path)
#    plt.close()
#    #faccio un nuovo istogramma per le colonne con molti zeri
#    conteggio_zeri = (df[col] == 0).sum()
#    percentuale_zeri = conteggio_zeri / len(df)
#    if percentuale_zeri>0.5:
#        df_senza_zeri = df[df[col] != 0]
#        plt.figure(figsize=(10, 15))
#        plt.hist(df_senza_zeri[col], bins=30, color='green', edgecolor='black')
#        plt.title(f'Istogramma di {col} (escludendo gli zeri)')
#        plt.xlabel(col)
#        plt.ylabel('Frequenza')
#        plt.tight_layout()
#        output_folder1 = os.path.join(output_folder, "no_zeri")
#        os.makedirs(output_folder1, exist_ok=True)
#        output_path = os.path.join(output_folder1, f"{col}_istogramma.png")
#        plt.savefig(output_path)
#        plt.close()
#    #faccio gli istogrammi senza outliers
#    df_senza_outliers = df[(df[col] >= (Q1[col] - 1.5 * IQR[col])) & (df[col] <= (Q3[col] + 1.5 * IQR[col]))]
#    plt.figure(figsize=(10, 15))
#    plt.hist(df_senza_outliers[col], bins=30, color='red', edgecolor='black')
#    plt.title(f'Istogramma di {col}')
#    plt.xlabel(col)
#    plt.ylabel('Frequenza')
#    plt.tight_layout()
#    output_folder1 = os.path.join(output_folder, "no_outliers")
#    os.makedirs(output_folder1, exist_ok=True)
#    output_path = os.path.join(output_folder1, f"{col}_istogramma.png")
#    plt.savefig(output_path)
#    plt.close()
#
##creo ed esporto i boxplots
#output_folder = os.path.join(ris_folder, "boxplots")
#os.makedirs(output_folder, exist_ok=True)
#for col in df[colonne_da_includere].select_dtypes(include='number').columns:
#    output_folder1 = os.path.join(output_folder, "normali")
#    os.makedirs(output_folder1, exist_ok=True)
#    output_path = os.path.join(output_folder1, f"{col}_boxplot.png")
#    plt.figure(figsize=(10, 15))
#    sns.boxplot(x=df[col], showfliers=True, color='skyblue')
#    plt.title(f"Boxplot di {col}")
#    plt.xlabel(col)
#    plt.ylabel("Frequenza")
#    plt.tight_layout()
#    plt.savefig(output_path)
#    plt.close()
#    #faccio un nuovo istogramma per le colonne con molti zeri
#    conteggio_zeri = (df[col] == 0).sum()
#    percentuale_zeri = conteggio_zeri / len(df)
#    if percentuale_zeri>0.5:
#        df_senza_zeri = df[df[col] != 0]
#        plt.figure(figsize=(10, 15))
#        sns.boxplot(x=df_senza_zeri[col], showfliers=True, color='green')
#        plt.title(f"Boxplot di {col}")
#        plt.xlabel(col)
#        plt.ylabel("Frequenza")
#        plt.tight_layout()
#        output_folder1 = os.path.join(output_folder, "no_zeri")
#        os.makedirs(output_folder1, exist_ok=True)
#        output_path = os.path.join(output_folder1, f"{col}_boxplot.png")
#        plt.savefig(output_path)
#        plt.close()
#    #ripeto anche senza outliers
#    output_folder1 = os.path.join(output_folder, "no_outliers")
#    os.makedirs(output_folder1, exist_ok=True)
#    output_path = os.path.join(output_folder1, f"{col}_boxplot.png")
#    plt.figure(figsize=(10, 15))
#    sns.boxplot(x=df[col], showfliers=False, color='red')
#    plt.title(f"Boxplot di {col}")
#    plt.xlabel(col)
#    plt.ylabel("Frequenza")
#    plt.tight_layout()
#    plt.savefig(output_path)
#    plt.close()
#
#creo ed esporto i kdeplot
output_folder = os.path.join(ris_folder, "kde_plots")
os.makedirs(output_folder, exist_ok=True)
for col in df[colonne_da_includere].select_dtypes(include='number').columns:
    output_folder1 = os.path.join(output_folder, "normali")
    os.makedirs(output_folder1, exist_ok=True)
    output_path = os.path.join(output_folder1, f"{col}_kdeplot.png")
    plt.figure(figsize=(10, 15))
    sns.kdeplot(df[col], shade=True, color="skyblue",fill=True)
    plt.title(f"KDE Plot di {col}")
    plt.xlabel(col)
    plt.ylabel("Densità")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    #faccio un nuovo istogramma per le colonne con molti zeri
    conteggio_zeri = (df[col] == 0).sum()
    percentuale_zeri = conteggio_zeri / len(df)
    if percentuale_zeri>0.5:
        df_senza_zeri = df[df[col] != 0]
        output_folder1 = os.path.join(output_folder, "no_zeri")
        os.makedirs(output_folder1, exist_ok=True)
        output_path = os.path.join(output_folder1, f"{col}_kdeplot.png")
        plt.figure(figsize=(10, 15))
        sns.kdeplot(df_senza_zeri[col], shade=True, color="green", fill=True)
        plt.title(f"KDE Plot di {col}")
        plt.xlabel(col)
        plt.ylabel("Densità")
        plt.tight_layout()
        plt.savefig(output_path)
        plt.close()
    #ripeto anche senza outliers
    output_folder1 = os.path.join(output_folder, "no_outliers")
    os.makedirs(output_folder1, exist_ok=True)
    output_path = os.path.join(output_folder1, f"{col}_kdeplot.png")
    df_senza_outliers = df[(df[col] >= (Q1[col] - 1.5 * IQR[col])) & (df[col] <= (Q3[col] + 1.5 * IQR[col]))]
    #funzione per vedere fare i kdeplot con per urban area con valori diversi 1.5
    plt.figure(figsize=(10, 15))
    sns.kdeplot(df_senza_outliers[col], shade=True, color="red", fill=True)
    plt.title(f"KDE Plot di {col}")
    plt.xlabel(col)
    plt.ylabel("Densità")
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
#
##creo ed esporto mappa di correlazione ed heatmap
#output_folder = os.path.join(ris_folder, "correlazioni_dispersioni")
#os.makedirs(output_folder, exist_ok=True)
#correlation_matrix = df[colonne_da_includere].select_dtypes(include='number').corr(numeric_only=True)
#output_path=os.path.join(output_folder, "matrice_correlazione.xlsx")
#correlation_matrix.to_excel(output_path)
#plt.figure(figsize=(12, 10))
#sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', fmt=".2f", square=True)
#plt.title("Correlation Heatmap")
#plt.tight_layout()
#output_path=os.path.join(output_folder, "correlation_heatmap.png")
#plt.savefig(output_path)
#plt.close()
#
#creo ed esporto i grafici a dipersione
#sns.pairplot(df[colonne_da_includere].select_dtypes(include='number'))
#output_path=os.path.join(output_folder,'pairplot.png')
#plt.savefig(output_path)
#plt.close()

#seleziono le features da me ritenute principali e calcolo l'importanza delle altre
#target_features=['IslandArea', 'Popolazione', 'solar_pow', 'eolico', 'gdp']
#output_folder = os.path.join(ris_folder, "importanza")
#os.makedirs(output_folder, exist_ok=True)
#
#for target_feature in target_features:
#    #seleziono le colonne
#    X = df[colonne_da_includere].select_dtypes(include='number').drop(columns=target_features)
#    y = df[target_feature]
#    #train/test
#    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
#    model = RandomForestRegressor(random_state=42)
#    model.fit(X_train, y_train)
#    #calcolo l'importanza delle features, creo un dataframe ordinato, creo un grafico e lo esporto
#    importances = model.feature_importances_
#    features = X.columns
#    feat_importance_df = pd.DataFrame({
#        'feature': features,
#        'importance': importances
#    }).sort_values(by='importance', ascending=False)
#    plt.figure(figsize=(12, 10))
#    sns.barplot(data=feat_importance_df, x='importance', y='feature', palette='viridis')
#    plt.title(f"Importanza delle features rispetto a '{target_feature}'")
#    plt.tight_layout()
#    output_path=os.path.join(output_folder, f'feature_importance_for_{target_feature}.png')
#    plt.savefig(output_path)
#    plt.close()

#analisi PCA
output_folder = os.path.join(ris_folder, 'PCA')
os.makedirs(output_folder, exist_ok=True)

col=['PC1','PC2','PC3','PC4']
X = df_clean.select_dtypes(include='number')
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
for j in ramge(2,5):
    pca = PCA(n_components=j)
    X_pca = pca.fit_transform(X_scaled)
    #dataframe con componenti principali
    df_pca = pd.DataFrame(X_pca, columns=col[:j])
    print(f"Il modello spiega questa quota di varianza: {pca.explained_variance_ratio_}")
    output_path = os.path.join(output_folder, f'analisys_df_{j}_components.pkl')
    df_pca.to_pickle(output_path)