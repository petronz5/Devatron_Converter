# cloud_integration.py

import os

"""
Esempio di integrazione con Google Drive attraverso PyDrive.
Richiede:
  pip install pydrive
e un file 'client_secrets.json' con le credenziali OAuth2.
"""

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def _get_drive():
    """
    Inizializza e restituisce un'istanza di GoogleDrive autenticata.
    """
    gauth = GoogleAuth()

    # Se hai un file client_secrets.json e vuoi usare un server web locale
    gauth.LocalWebserverAuth()  # aprirà il browser per login

    # Crea l'oggetto drive
    return GoogleDrive(gauth)

def upload_to_google_drive(file_path):
    """Carica un file su Google Drive e ritorna l'ID del file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError("File non esistente")

    drive = _get_drive()
    file_drive = drive.CreateFile({'title': os.path.basename(file_path)})
    file_drive.SetContentFile(file_path)
    file_drive.Upload()
    return f"File caricato su Drive con ID: {file_drive['id']}"

def download_from_google_drive(file_id, output_path):
    """Scarica un file dal Drive usando l'ID."""
    drive = _get_drive()
    file_drive = drive.CreateFile({'id': file_id})
    file_drive.GetContentFile(output_path)
    return f"File scaricato da Drive in: {output_path}"
