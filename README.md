Il seguente progetto ha l'obiettivo di raccogliere dati riguardo le isole del mondo al fine di realizzare una clusterizzazione. I dati raccolti riguardano aspetti di natura socioeconomica e risorse naturali. L'obiettivo del progetto è quello di suddividere le isole in clusters basati sulle opportunità e difficoltà del percorso di transizione energetica. Le isole degli stessi clusters avranno caratteristiche simili e, in linea di massima, dovranno seguire strategie simili nel processo di transizione. In questa ottica un'isola indietro in questo processo potrebbe prendere esempio dalle strategie adottate da un'altra isola dello stesso cluster più avanti nel percorso.

# Definizione delle isole
Le isole sono prese dal seguente sito https://www.sciencebase.gov/catalog/item/63bdf25dd34e92aad3cda273. Il progetto in questione, realizzato dall'USGS, ente governativo statunitense fornitore di servizi geologici, mette a disposizione un file in formato mpk contenente tutte le isole del mondo. Il file è stato estratto mediante l'ausilio dell'applicazione 7zip. Attraverso il QGIS, software open source per la manipolazione e visualizzazione di dati spaziali e geografici. Il file presenta quattro livelli:
-placche contientali
-big islands (superficie>1km2)
-small islands (0.0036km2 < superficie < 1km2)
-very small islands (superficie < 0.0036km2)
Le uniche isole di nostro interesse sono le seconde, le altre non sono abbastanza rilevanti per il nostro studio. Ho selezionato il gruppo in questione e l'ho esportato come file gpkg, di più facile manipolazione.

Per scaricare i vari files del progetto (tra cui questo delle isole) è necessario runnare il programma src/1-files/files.py che avvierà il download dei files caricati in una cartella google drive e li posizionaerà nella cartella del progetto opportuna. Lo script in questione deve essere il primo ad essere girato poiché gli script successivi necessitano dei vari files per essere eseguiti.
All'interno dello script files è presente il comando per svolgere l'autenticazione alle API google earth, necessaria per scaricare alcuni dati. Durante la run si aprirà la pagina per effettuare il login e verrà creata una cartella con il file delle credenziali all'interno del pc dell'utente. Serve anche creare un progetto google cloud (https://console.cloud.google.com/earth-engine/welcome?hl=it) e inserire il nome del progetto creato nel file config associandolo alla variabile project.

Riporto i files caricati e le API usate e i relativi link di riperimento:
-isole_4326.gpkg, procedimento precedente
-popolazione.tif https://landscan.ornl.gov/
-PVOUT.tif e PVOUT_month.tif https://datacatalog.worldbank.org/search/dataset/0038641/World---Photovoltaic-Power-Potential--PVOUT--GIS-Data---Global-Solar-Atlas-
-eolico, https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_DAILY?hl=it, https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_DAILY_AGGR?hl=it
-shapefiles relativi all'offshore https://datacatalog.worldbank.org/search/dataset/0037787/Global-Offshore-Wind-Technical-Potential
-urban, https://developers.google.com/earth-engine/datasets/catalog/JRC_GHSL_P2023A_GHS_SMOD_V2-0?hl=it
-elevazione, https://developers.google.com/earth-engine/datasets/catalog/USGS_GMTED2010_FULL?hl=it
https://developers.google.com/earth-engine/datasets/catalog/JAXA_ALOS_AW3D30_V3_2?hl=it
-temperatura, precipitazioni, heating days, cooling days https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_DAILY, https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_MONTHLY
-GDP.tif, https://www.ngdc.noaa.gov/eog/dmsp/download_gdp.html
-nightlights https://developers.google.com/earth-engine/datasets/catalog/NOAA_VIIRS_DNB_ANNUAL_V22
-protected areas https://developers.google.com/earth-engine/datasets/catalog/WCMC_WDPA_current_polygons?hl=it
-elevazione, https://developers.google.com/earth-engine/datasets/catalog/JAXA_ALOS_AW3D30_V3_2?hl=it
-copertura terreni, https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global?hl=it
-evi, https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MOD13A3?hl=it
-geothermal_potential.gpkg, https://dataservices.gfz-potsdam.de/panmetaworks/showshort.php?id=e6755429-fbbf-11ee-967a-4ffbfe06208e
-hydro.gpkg, https://data.4tu.nl/articles/dataset/Global_potential_hydropower_locations/12708413
-nazioni del mondo, https://developers.google.com/earth-engine/datasets/catalog/FAO_GAUL_SIMPLIFIED_500m_2015_level0?hl=it

# Prelavori sulle isole
Gli script all'interno della cartella src/2-preprocessing_isole vanno eseguiti subito dopo aver scaricato i files. Gli altri script si baseranno sugli output di questi. Gli script in questa cartella vanno eseguiti in sequenza in base al numero che precede il loro titolo. Le operazioni svolte consistono in:
-due filtraggi basati su popolazione e superficie, al fine di selezionare le isole sufficientemente rilevanti (popolazione e superficie maggiore dei valori minimi) e i cui sistemi energetici mantengano caratteristiche insulari più che continentali (popolazione e superficie minore dei valori massimi). I dati sulla popolazione sono contenuti all'interno di un file GEOTIFF realizzato dall' OAK RIDGE NATIONAL LABORATORY, laboratorio di ricerca statunitense.
-arrotondamento delle coordinate dei poligoni a due, tre, quattro cifre decimali, per alcune operazioni non è richiesta una risoluzione spaziale così fine e i files ottenuti risultano molto più leggeri e maneggevoli.
-creazione del dizionario associante a ogni isola le nazioni che la contengono, necessario per lo script sull'eolico offshore che associa le zone marine alla nazione di autorità.

# Dati solari
I dati in questione sono presentati in formato GEOTIFF e sono un'elaborazione di IRENA, ente dell'ONU che si occupa di energie rinnovabili. L'elaborazione si basa sui dati di irradiazione del World Solar Atlas e va a stimare la producibilità di un impianto fotovoltaico in ogni punto del file. Per producibilità si intende il rapporto tra energia e prodotta in un giorno e potenza dell'impianto, calcolata in KWh/KW. I files in questione sono diversi: uno riguarda la producibilità media annuale, una cartella contiene i files relativi alla producibilità media dei singoli mesi per stimare la varianza della media mensile di questa grandezza. Lo script calcola per ogni isola il valore medio dei pixel all'interno dei files. I parametri considerati sono la producibilità media annuale e la varianza della producibilità media mensile. Questa è considerata perchè legata agli investimenti che l'isola dovrà effettuare in termini di storage.

# Dati eolico (da riscrivere e aggiungere offshore)
Raccolti dal dataset ERA5-Land e, in caso questo non coprisse l'isola, dal dataset ERA5, entrambi prodotti da Copernicus, programma di osservazione spaziale dell'UE. Per ogni isola è stata considerata la media del cubo della velocità del vento, grandezza proporzionale alla potenza del vento stesso. Sono stati considerati anche i mesi singolarmente per calcolare la deviazione standard della media mensile di questa grandezza, per lo stesso motivo del fotovoltaico.
Per l'offshore gli shapefiles sono realizzati da IRENA e fanno una stima della potenza installabile in una regione tenendo conto dei fondali e della potenza del vento. L'analisi svolta associa ogni isola alla nazione/nazioni che la contiene/contengono e, nel caso fosse contenuta in una zona offshore appartenente alla stessa nazione associa all'isola una frazione della potenza della shape in questione.

# Superficie urbana
Dati scaricati dal GHSL, progetto finanziato dall'UE, mediante le API Google Earth. Il dataset associa a ogni pixel un valore in base alla densità urbana calcolata.

# Temperatura, precipitazioni, heating e cooling days
Dati estratti mediante l'API di google earth engine che raccoglie dati raccolti da altri enti. Questi in particolare provengono dal database ERA5, realizzato da Copernicus, ente finanziato dall'UE. Per hdd e cdd i valori sono calcolati nello script a partire dalle temperature medie giornaliere.

# GDP
Il file è in formato GEOTIFF, realizzato dal NOAA, centro governativo statunitense e riporta stime dell'attività economica nei vari punti geografici basate sull'illuminazione notturna registrata via satellite. La raccolta si basa su uno studio svolto che individua correlazioni tra luci notturne e attività economica. Dati aggiornati al 2010.

# Nightlights (da riscrivere)
Alla luce della correlazione precedente ho pensato di raccogliere personalmente dati relativi all'illuminazione notturna per avere valori aggiornati e recenti. Ho notato varianze significative fra due anni consecutivi, mi ha fatto dubitare dell'affidabilità o della necessità di eseguire qualche operazione tra i dati raccolti.

# Biomassa
Dati scaricati dal dataset MODIS, realizzato dalla NASA, mediante le API Google Earth. Il parametro considerato è l'EVI un indicatore che riassume le proprietà della vegetazione di una regione.

# Geothermal
Il file scaricabile dal link consiste in un file .xlsx. Dopo aver eliminato delle colonne inutili ai fini del nostro progetto, il file è stato convertito in formato .csv per potere essere aperto in QGIS. Tramite QGIS è stato nuovamente covertito in formato .gpkg prima di eseguire un'operazione di intersezione sulle isole cui avevo applicato un buffer di 30000 metri (i siti geotermici possono anche essere realizzati offshore). In questo modo ho ridotto le dimensioni del file e il numero dei suoi elementi conservando le righe rilevanti per alleggerire il carico computazionale.

# Hydro
Il file scaricabile al link è in formato .shp. Anche in questo caso è stato aperto in QGIS, convertito in gpkg e ne è stat calcolata l'intersezione con le isole al fine di considerare solo i siti rilevanti al progetto e allegerire il file.

# % superficie RES e elevazione
I dati sono stati scaricati dai dataset WDPA: World Database on Protected Areas, ALOS DSM: Global 30m v3.2 e Copernicus Global Land Cover Layers: CGLS-LC100 Collection 3 tramite le API Google Earth. Lo script elimina le aree non agibili per realizzare impianti rinnovabili quali corpi acquatici, zone protette, zone con altitudine o pendenza elevata. Lo script calcola anche l'elevazione massima di ogni isola.


Nella cartella \data\dati_finali ho caricato i files .pkl finali, ottenuti tramite la run dei vari script.