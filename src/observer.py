import websocket
import logging
import os
import json
import threading

# Lista delle criptovalute da osservare (esempio con 10 coppie)
CRYPTO_PAIRS = [
    "btcusdt", "ethusdt", "bnbusdt", "adausdt", "xrpusdt",
    "solusdt", "dotusdt", "dogeusdt", "maticusdt", "linkusdt"
]

# URL del WebSocket di Binance per le coppie selezionate
STREAM_URL = f"wss://stream.binance.com:9443/ws/{'/'.join([f'{pair}@ticker' for pair in CRYPTO_PAIRS])}"

# Classe personalizzata per gestire il flush e commit immediati dei log
class FlushFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()
        os.fsync(self.stream.fileno())

# Configurazione del logging con flush immediato
logging.basicConfig(
    handlers=[FlushFileHandler("log/crypto_price_log.log")],
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Funzione per gestire i messaggi ricevuti dal WebSocket
def on_message(ws, message):
    try:
        data = json.loads(message)
        symbol = data.get("s")
        price = data.get("c")
        high_price = data.get("h")
        low_price = data.get("l")
        volume = data.get("v")
        if symbol and price:
            log_message = json.dumps({
                "symbol": symbol,
                "price": price,
                "high": high_price,
                "low": low_price,
                "volume": volume
            })
            logging.info(log_message)
    except Exception as e:
        logging.error(f"Error processing message: {e}")

# Funzione per gestire eventuali errori del WebSocket
def on_error(ws, error):
    logging.error(f"WebSocket Error: {error}")

# Funzione per gestire la chiusura del WebSocket
def on_close(ws, close_status_code, close_msg):
    logging.info("WebSocket closed")

# Funzione per iniziare la connessione WebSocket
def on_open(ws):
    logging.info("WebSocket connection opened")

# Avvio del WebSocket in un thread separato
def start_websocket():
    ws = websocket.WebSocketApp(
        STREAM_URL,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open
    ws.run_forever()

if __name__ == "__main__":
    try:
        # Avvia il WebSocket in un thread separato
        threading.Thread(target=start_websocket, daemon=True).start()
        # Mantieni il programma in esecuzione
        input("Premi Ctrl+C per interrompere il programma...\n")
    except KeyboardInterrupt:
        print("Programma interrotto dall'utente.")
