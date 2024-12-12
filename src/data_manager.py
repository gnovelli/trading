import pandas as pd
import json

def load_data(log_file):
    """
    Carica i dati dal file di log e li converte in un DataFrame pandas.

    :param log_file: Percorso del file di log.
    :return: pandas.DataFrame contenente i dati caricati.
    """
    data = []
    try:
        with open(log_file, 'r') as file:
            for line in file:
                if '{' in line:
                    try:
                        log_entry = json.loads(line.split(' - ')[-1])
                        data.append({
                            'symbol': log_entry['symbol'],
                            'price': float(log_entry['price']),
                            'high': float(log_entry['high']),
                            'low': float(log_entry['low']),
                            'volume': float(log_entry['volume'])
                        })
                    except json.JSONDecodeError as e:
                        print(f"Errore nel parsing della riga: {e}")
    except FileNotFoundError:
        print(f"Il file di log {log_file} non è stato trovato.")
    except Exception as e:
        print(f"Errore generico durante il caricamento dei dati: {e}")

    return pd.DataFrame(data)
