import json
import os
from datetime import datetime

def log_conversion(username, input_path, output_path):
    """
    Salva la conversione in un file JSON di cronologia personale per l'utente specificato.
    """
    record = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "input": input_path,
        "output": output_path
    }

    # Costruiamo il nome del file di cronologia in base allo username
    history_file = f"history_{username}.json"

    # Leggi eventuale cronologia esistente
    if os.path.exists(history_file):
        with open(history_file, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if not isinstance(data, list):
                    data = []
            except:
                data = []
    else:
        data = []
    
    # Aggiungi la nuova entry in testa, così l'ultima conversione è in cima
    data.insert(0, record)
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
