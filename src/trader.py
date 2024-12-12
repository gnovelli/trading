from data_manager import load_data
from trainer import train_agent, test_agent
from crypto_env import CryptoTradingEnv  # Import corretto dell'ambiente di trading
import time

if __name__ == "__main__":
    log_file = "log/crypto_price_log.log"
    
    data = load_data(log_file)
    if data.empty:
        print("Nessun dato trovato nel file di log.")
        exit(1)

    env = CryptoTradingEnv(data)

    while True:
        print("\n===== Inizio Training =====")
        q_table = train_agent(env, episodes=1000)
        
        print("\n===== Inizio Testing =====")
        test_agent(env, q_table)
        
        print("\nTraining e Testing completati. Riinizio tra 10 secondi...\n")
        time.sleep(10)
