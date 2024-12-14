from data_manager import load_data
from trainer import train_agent, test_agent
from crypto_env import CryptoTradingEnv  # Correct import of the trading environment
import time

if __name__ == "__main__":
    # Path to the log file containing cryptocurrency data
    log_file = "log/crypto_price_log.log"
    
    # Load data from the log file
    data = load_data(log_file)
    if data.empty:
        print("No data found in the log file.")
        exit(1)  # Exit the program if no data is available

    # Initialize the trading environment with the loaded data
    env = CryptoTradingEnv(data)

    # Infinite loop to continuously train and test the agent
    while True:
        print("\n===== Starting Training =====")
        q_table = train_agent(env, episodes=1000)  # Train the agent for 1000 episodes
        
        print("\n===== Starting Testing =====")
        test_agent(env, q_table)  # Test the agent using the trained Q-table
        
        print("\nTraining and Testing completed. Restarting in 10 seconds...\n")
        time.sleep(10)  # Wait for 10 seconds before restarting the process
