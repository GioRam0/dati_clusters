#importo le librerie
import requests
import os
import sys
from bs4 import BeautifulSoup
import pickle
import ee

#svolgere l'autenticazione alle API Google Earth, fatta la prima volta salva l'accesso e crea una cartella config con i token nel pc dell'utente
#dopo l'autenticazione è necessario creare un progetto google cloud (https://console.cloud.google.com/earth-engine/welcome?hl=it)
#ed inserire il nome del progetto nel file config.py alla variabile project
ee.Authenticate()

# cartella in cui si trova lo script
cartella_corrente = os.path.dirname(os.path.abspath(__file__))
cartella_progetto = os.path.join(cartella_corrente, "..", "..")

# percorso file config
percorso_config = os.path.join(cartella_corrente, "..", "config.py")
sys.path.append(os.path.dirname(percorso_config))
#importo le variabili config
import config
#dizionario con gli ID dei files nella cartella drive e il nome che devono avere nella cartella di destinazione
files = config.FILES
#lista dei files già scaricati
file_pkl=os.path.join(cartella_corrente,"downloaded_files.pkl")
if os.path.exists(file_pkl):
    try:
        with open(file_pkl, 'rb') as file:
            downloaded_files = pickle.load(file)
        print("Lista caricata con successo dal file downloaded_files.pkl.")
    except Exception as e:
        print(f"Errore durante il caricamento del file downloaded_files.pkl: {e}")
        downloaded_files = []
else:
    downloaded_files=[]
print(downloaded_files)

folder_out = os.path.join(cartella_progetto, "files")
os.makedirs(folder_out, exist_ok=True)
folder_out1 = os.path.join(folder_out, "PVOUT_month")
os.makedirs(folder_out1, exist_ok=True)

def download_file(file_id, file_name):
    url = "https://drive.google.com/uc?export=download"
    session = requests.Session()
    if file_name.startswith("PVOUT_"):
        file_path = os.path.join(folder_out1, file_name)
    else:
        file_path = os.path.join(folder_out, file_name)
    try:
        response = session.get(url, params={"id": file_id}, stream=True, allow_redirects=True)
        response.raise_for_status()
        if "Virus scan warning" in response.text:
            soup = BeautifulSoup(response.text, 'html.parser')
            download_form = soup.find('form', {'id': 'download-form'})
            if download_form:
                download_url = download_form.get('action')
                form_data = {}
                for input_tag in download_form.find_all('input'):
                    name = input_tag.get('name')
                    value = input_tag.get('value')
                    if name:
                        form_data[name] = value
            download_response = requests.get(download_url, params=form_data, stream=True)
            download_response.raise_for_status()
            with open(file_path, "wb") as f:
                for chunk in download_response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"File scaricato con successo come: {file_name}")
        else:
            with open(file_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"File scaricato con successo come: {file_name}")
        downloaded_files.append(file_id)
    except requests.exceptions.RequestException as e:
        print(f"Errore durante il download: {e}")
    except Exception as e:
        print(f"Si è verificato un errore: {e}")

#applico la funzione agli elementi del dizionario non ancora scaricati
for file_id, file_name in files.items():
    if file_id not in downloaded_files:
        download_file(file_id, file_name)
#controllo che siano stati scaricati tutti gli elementi
if len(files)==len(downloaded_files):
    print('Tutti i files sono stati scaricati correttamente')
else:
    print('Non tutti i files sono stati scaricati correttamente, rilanciare lo script.')
#aggiorno gli elementi scaricati
with open(file_pkl, "wb") as f:
    pickle.dump(downloaded_files, f)