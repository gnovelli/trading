import websocket
import logging
import os
import json
import threading

# List of cryptocurrencies to monitor
CRYPTO_PAIRS = [
    "btcusdt", "ethusdt", "bnbusdt", "adausdt", "xrpusdt",
    "solusdt", "dotusdt", "dogeusdt", "maticusdt", "linkusdt"
]

# Binance WebSocket URL for the selected cryptocurrency pairs
STREAM_URL = f"wss://stream.binance.com:9443/ws/{'/'.join([f'{pair}@ticker' for pair in CRYPTO_PAIRS])}"

# Custom class to handle immediate flushing and committing of log data
class FlushFileHandler(logging.FileHandler):
    def emit(self, record):
        super().emit(record)
        self.flush()
        os.fsync(self.stream.fileno())  # Ensures log data is written immediately to disk

# Logging configuration with immediate flush
logging.basicConfig(
    handlers=[FlushFileHandler("log/crypto_price_log.log")],
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Function to handle incoming WebSocket messages
def on_message(ws, message):
    try:
        data = json.loads(message)  # Parse the JSON message
        symbol = data.get("s")      # Symbol of the cryptocurrency
        price = data.get("c")       # Current price
        high = data.get("h")        # Highest price
        low = data.get("l")         # Lowest price
        volume = data.get("v")      # Trading volume

        # Log the message if symbol and price are present
        if symbol and price:
            log_entry = json.dumps({
                "symbol": symbol,
                "price": price,
                "high": high,
                "low": low,
                "volume": volume
            })
            logging.info(log_entry)  # Write the log entry to the log file
    except Exception as e:
        logging.error(f"Error processing message: {e}")

# Function to handle WebSocket errors
def on_error(ws, error):
    logging.error(f"WebSocket Error: {error}")

# Function to handle WebSocket closure
def on_close(ws, close_status_code, close_msg):
    logging.info("WebSocket closed")

# Function to handle the opening of the WebSocket connection
def on_open(ws):
    logging.info("WebSocket connection opened")

# Start the WebSocket in a separate thread
def start_websocket():
    ws = websocket.WebSocketApp(
        STREAM_URL,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    ws.on_open = on_open  # Assign the on_open handler
    ws.run_forever()      # Keep the connection running indefinitely

# Entry point of the script
if __name__ == "__main__":
    try:
        # Start the WebSocket connection in a separate daemon thread
        threading.Thread(target=start_websocket, daemon=True).start()
        input("Press Ctrl+C to stop the program...\n")
    except KeyboardInterrupt:
        print("Program interrupted by user.")
