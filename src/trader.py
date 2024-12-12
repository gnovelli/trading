import gymnasium as gym
import numpy as np
import pandas as pd
import json
import os
import time
from gymnasium import spaces
import random
from joblib import Parallel, delayed
import matplotlib.pyplot as plt

# Carica i dati dal file di log
def load_data(log_file):
    data = []
    with open(log_file, 'r') as file:
        for line in file:
            try:
                if '{' in line:
                    log_entry = json.loads(line.split(' - ')[-1])
                    data.append({
                        'symbol': log_entry['symbol'],
                        'price': float(log_entry['price']),
                        'high': float(log_entry['high']),
                        'low': float(log_entry['low']),
                        'volume': float(log_entry['volume'])
                    })
            except Exception as e:
                pass  # Ridotto debug
    return pd.DataFrame(data)

# Environment personalizzato per il trading
class CryptoTradingEnv(gym.Env):
    def __init__(self, data):
        super(CryptoTradingEnv, self).__init__()
        self.data = data
        self.current_step = 0
        self.balance = 1000  # Capitale iniziale
        self.crypto_holdings = 0
        self.total_value = self.balance
        self.commission = 0.001  # Commissione dello 0.1%
        
        # Definizione degli spazi di azione e osservazione
        self.action_space = spaces.Discrete(3)  # 0 = Hold, 1 = Buy, 2 = Sell
        self.observation_space = spaces.Box(
            low=0, high=np.inf, shape=(4,), dtype=np.float32
        )

    def reset(self, seed=None):
        self.current_step = 0
        self.balance = 1000
        self.crypto_holdings = 0
        self.total_value = self.balance
        return self._get_observation(), {}

    def _get_observation(self):
        current_price = self.data.iloc[self.current_step]['price']
        high = self.data.iloc[self.current_step]['high']
        low = self.data.iloc[self.current_step]['low']
        volume = self.data.iloc[self.current_step]['volume']
        return np.array([current_price, high, low, volume], dtype=np.float32)

    def step(self, action):
        current_price = self.data.iloc[self.current_step]['price']
        previous_price = current_price  # Inizializza previous_price per evitare l'errore
        
        # Azioni: 0 = Hold, 1 = Buy, 2 = Sell
        if action == 1 and self.balance >= current_price * (1 + self.commission):
            self.crypto_holdings += 1
            self.balance -= current_price * (1 + self.commission)
        elif action == 2 and self.crypto_holdings > 0:
            self.crypto_holdings -= 1
            self.balance += current_price * (1 - self.commission)

        self.total_value = self.balance + self.crypto_holdings * current_price
        self.current_step += 1

        done = self.current_step >= len(self.data) - 1
        
        # Penalità per mantenere troppe criptovalute durante una tendenza al ribasso
        trend_penalty = 0
        if self.crypto_holdings > 0 and self.current_step > 0:
            previous_price = self.data.iloc[self.current_step - 1]['price']
            if current_price < previous_price:
                trend_penalty = -self.crypto_holdings * abs(current_price - previous_price)
        
        reward = (self.total_value - (self.balance + self.crypto_holdings * previous_price)) + trend_penalty  # Ricompensa relativa con penalità
        reward /= 1000  # Normalizzazione del reward

        return self._get_observation(), reward, done, False, {}

    def render(self):
        print(f"Step: {self.current_step}, Balance: {self.balance:.2f}, Holdings: {self.crypto_holdings}, Total Value: {self.total_value:.2f}")

# Funzione per addestrare l'agente con Q-Learning
def train_single_episode(env, q_table, alpha, gamma, epsilon):
    state, _ = env.reset()
    done = False
    
    while not done:
        if random.uniform(0, 1) < epsilon:
            action = env.action_space.sample()
        else:
            action = np.argmax(q_table[env.current_step])

        next_state, reward, done, _, _ = env.step(action)

        # Penalità aggiuntiva per azioni non produttive
        if action == 0 and env.current_step > 0:
            current_price = env.data.iloc[env.current_step]['price']
            previous_price = env.data.iloc[env.current_step - 1]['price']
            if current_price < previous_price:
                reward -= 5

        q_table[env.current_step, action] += alpha * (
            reward + gamma * np.max(q_table[env.current_step]) - q_table[env.current_step, action]
        )

def train_agent(env, episodes=500, alpha=0.1, gamma=0.99, epsilon=0.1):
    q_table = np.zeros((len(env.data), env.action_space.n))
    epsilon_decay = epsilon
    for episode in range(episodes):
        train_single_episode(env, q_table, alpha, gamma, epsilon_decay)
        epsilon_decay = max(0.01, epsilon_decay * 0.99)  # Decay di epsilon
        if episode % 100 == 0:
            print(f"Completed Episode {episode}/{episodes}")
    return q_table

# Funzione per testare l'agente
def test_agent(env, q_table):
    state, _ = env.reset()
    done = False
    performance = []

    while not done:
        action = np.argmax(q_table[env.current_step])
        state, reward, done, _, _ = env.step(action)
        performance.append(env.total_value)
        env.render()
    
    plot_performance(performance)

def plot_performance(performance):
    plt.plot(performance)
    plt.xlabel('Step')
    plt.ylabel('Total Value')
    plt.title('Trading Performance')
    plt.show()

# Main per eseguire il ciclo continuo di training e testing
if __name__ == "__main__":
    log_file = "log/crypto_price_log.log"
    
    if not os.path.exists(log_file):
        print(f"File di log non trovato: {log_file}")
        exit(1)
    
    data = load_data(log_file)
    if data.empty:
        print("Nessun dato trovato nel file di log.")
        exit(1)

    env = CryptoTradingEnv(data)

    while True:
        print("\n===== Inizio Training =====")
        q_table = train_agent(env, episodes=200)
        
        print("\n===== Inizio Testing =====")
        test_agent(env, q_table)
        
        print("\nTraining e Testing completati. Riinizio tra 10 secondi...\n")
        time.sleep(10)

