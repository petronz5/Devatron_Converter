import os
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def _init_drive():
    """
    Inizializza l'autenticazione con Google Drive.
    Se esistono token validi (in credentials.json) non chiede nuovamente il login.
    """
    gauth = GoogleAuth()
    if not os.path.exists("client_secrets.json"):
        raise FileNotFoundError("File client_secrets.json non trovato. Scarica le credenziali dalla Google Cloud Console e posizionale nella cartella del progetto.")
    gauth.LocalWebserverAuth()
    return GoogleDrive(gauth)

def upload_to_drive(file_path):
    """Carica un file su Drive, ritorna l'ID del file."""
    if not os.path.exists(file_path):
        raise FileNotFoundError("Il file non esiste.")
    drive = _init_drive()
    file_drive = drive.CreateFile({'title': os.path.basename(file_path)})
    file_drive.SetContentFile(file_path)
    file_drive.Upload()
    return f"Caricato su Drive con ID: {file_drive['id']}"

def download_from_drive(file_id, output_path):
    """Scarica un file da Drive (tramite ID)."""
    drive = _init_drive()
    file_drive = drive.CreateFile({'id': file_id})
    file_drive.GetContentFile(output_path)
    return f"File Drive {file_id} scaricato in {output_path}"
