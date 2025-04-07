Il seguente progetto ha l'obiettivo di raccogliere dati riguardo le isole del mondo al fine di realizzare una clusterizzazione. I dati raccolti riguardano aspetti di natura socioeconomica e di risorse naturali. L'obiettivo del progetto è quello di suddividere le isole in clusters basati sulle opportunità e difficoltà del percorso di transizione energetica. Le isole degli stessi clusters avranno caratteristiche di simili e, in linea di massima, dovranno seguire strategie simili nel processo di transizione. In questa ottica un'isola indietro in questo processo potrebbe prendere esempio dalle strategie adottate da un'altra isola dello stesso cluster più avanti nel percorso.

# Definizione delle isole

Le isole sono prese dal seguente sito https://www.sciencebase.gov/catalog/item/63bdf25dd34e92aad3cda273. Il progetto in questione, realizzato dall'USGS, ente governativo statunitense fornitore di servizi geologici, mette a disposizione un file in formato mpk contenente tutte le isole del mondo. Il file è stato estratto mediante l'ausilio dell'applicazione 7zip. Attraverso il QGIS, software open source per la manipolazione e visualizzazione di dati spaziali e geografici. Il file presenta quattro livelli:
-placche contientali
-big islands (superficie>1km2)
-small islands (0.0036km2 < superficie < 1km2)
-very small islands (superficie < 0.0036km2)
Le uniche isole di nostro interesse sono le seconde, le altre non sono abbastanza rilevanti per il nostro studio. Ho selezionato il gruppo in questione e l'ho esportato come file gpkg, di più facile manipolazione.

Per scaricare i vari files del progetto (tra cui questo delle isole) è necessario runnare il programma src/1-files/files.py che avvierà il download dei file caricati in una cartella google drive e li posizionaerà nella cartella del progetto opportuna. Il file in questione deve essere il primo ad essere girato poiché gli script successivi necessitano dei vari files.

Riporto i files caricati e le API usate e i relativi link di riperimento:
-isole_4326.gpkg, procedimento precedente
-popolazione.tif https://landscan.ornl.gov/
-PVOUT.tif e PVOUT_month.tif https://datacatalog.worldbank.org/search/dataset/0038641/World---Photovoltaic-Power-Potential--PVOUT--GIS-Data---Global-Solar-Atlas-
-global_power_density.tif https://datacatalog.worldbank.org/search/dataset/0038643/World---Wind-Speed-and-Power-Density-GIS-Data
-urban_isl.gpkg https://www.earthdata.nasa.gov/data/catalog/sedac-ciesin-sedac-grumpv1-ext-1.00, necessario creare un account gratuito earthdata
-elevazione
-temperatura, precipitazioni, heating days, cooling days https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_DAILY, https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_MONTHLY
-GDP.tif, https://www.ngdc.noaa.gov/eog/dmsp/download_gdp.html
-nightlight https://developers.google.com/earth-engine/datasets/catalog/NOAA_VIIRS_DNB_ANNUAL_V22

# Prelavori sulle isole

Gli script all'interno della cartella src/2-preprocessing_isole vanno subito dopo aver scaricato i files in quanto gli altri script si baseranno sugli output di questi. Gli script in questa cartella vanno eseguiti in sequenza in base al numero che precede il loro titolo. Le operazioni svolte consistono in:
-due filtraggi basati su popolazione e superficie, al fine di selezionare le isole sufficientemente rilevanti (valori minimi) e i cui sistemi energetici mantengano caratteristiche insulari più che continentali. I dati sulla popolazione sono contenuti all'interno di un file GEOTIFF scaricato dal seguente sito https://landscan.ornl.gov/ e raccolti dall' OAK RIDGE NATIONAL LABORATORY, rinomato laboratorio di ricerca statunitense.
(in questa versione light ho aumentato i limiti minimi e diminuito quelli massimi per ridurre il numero di isole)
-arrotondamento delle coordinate dei poligoni a due cifre decimali, quanto per molte operazioni non è richiesta una risoluzione spaziale così fine e il file risulta molto più leggero e maneggevole.

# Dati solari
I dati in questione sono presentati in formato GEOTIFF e sono un'elaborazione di IRENA, ente dell'ONU che si occupa di energie rinnovabili. L'elaborazione si basa sui dati di irradiazione del World Solar Atlas e va a stimare la producibilità di un impianto fotovoltaico in ogni punto del file. Per producibilità si intende il rapporto tra energia e prodotta in un giorno e potenza dell'impianto, calcolata in KWh/KW. I files in questione sono diversi: uno riguarda la producibilità media annuale, una cartella contiene i files relativi alla producibilità media dei singoli mesi per stimare la varianza della media mensile di questa grandezza. Lo script calcola per ogni isola il valore medio dei pixel all'interno dei files. I parametri considerati sono la producibilità media annuale e la varianza della producibilità media mensile. Questa è considerata perchè legata agli investimenti che l'isola dovrà effettuare in termini di storage.

# Dati eolico
Anche in questo caso i dati provengono da elaborazioni IRENA e stimano la potenza teoricamente estraibile dal vento rapportata alla superficie (W/m2). IRENA non fornisce dati sulle medie dei singoli mesi.

# Superficie urbana
I dati in questione sono scaricati dal portal earthdata della NASA. Sono scaricati in formati shapefile. Con l'ausilio di QGIS ho conservato solo le figure che intersecavno le isole da noi considerate e ho esportato il file in formato gpkg al fine di alleggerire il carico computazionle. Il file della NASA ad ora non è scaricabile a causa di manutenzione/aggiornamento di server. Avrei trovato un altro file ma non riporta aree urbane sotto una certa dimensione e quindi alcune isole sono scoperte (file sempre in formato .shp ed esportato in gpkg tramite QGIS). Ad ora ho caricato il file earthdata.

# Elevazione
Anche questo file è fornito dal Global Solar Atlas.

# Temperatura, precipitazioni, heating e cooling days
Dati estratti mediante l'API di google earth engine che raccoglie dati raccolti da altri enti. Questi in particolare provengono dal database ERA5, realizzato da Copernicus, ente finanziato dall'UE. Per hdd e cdd i valori sono calcolati nello script a partire dalle temperaturemedie giornaliere. Gli script hdd_cdd e hdd_cdd2 vanno eseguiti in sequenza.

# GDP
Il file è in formato GEOTIFF, realizzato dal NOAA, centro governativo statunitense e riporta stime dell'attività economica nei vari punti geografici basate sull'illuminazione notturna registrata via satellite. La raccolta si basa su uno studio svolto che individua correlazioni tra luci notturne e attività economica. Dati aggiornati al 2010.

# Nightlights
Alla luce della correlazione precedente ho pensato di raccogliere personalmente dati relativi all'illuminazione notturna per avere valori aggiornati e recenti. Ho notato varianze significative fra due anni consecutivi, mi ha fatto dubitare dell'affidabilità o della necessità di eseguire qualche operazione tra i dati raccolti.

# Potential offshore
https://datacatalog.worldbank.org/search/dataset/0037787/Global-Offshore-Wind-Technical-Potential
da qua possono essere scaricati i file .shp con i potenziali tecnici stimati di potenziale installabile nei vari poligoni e l'appartenenza della competenza economica

# test atlite
Lo script servirebbe per scaricare dati sia meteorologici, sia solari, sia eolici. https://github.com/PyPSA/atlite questo il link della libreria. Nello script prevedevo di usare i dati ERA5 ma al momento i loro server sono in manutenzione e non si riesce ad eseguire la richiesta API. Questo mi impedisce di testare le funzionalita e completare il codice. Per scaricare i dati ERA5 tramite atlite occorre scaricare la libreria cdsapi (compare nel requiremets.txt), creare un profilo gratuito cds https://cds.climate.copernicus.eu/ e creare un file senza estensione intitolato .cdsapirc nella cartella "C:\Users\Nome_utente", putroppo questo file non può essere inserito nell'enviroment e l'utente lo deve realizzare da solo. Il file deve contenere due righe di codice così scritte:
url: https://cds.climate.copernicus.eu/api
key: <API-KEY>
La API-KEY si può reperire dal proprio profilo CDS.