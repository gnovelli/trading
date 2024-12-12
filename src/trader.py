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

# Carica i dati dal file di log per più criptovalute
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

# Environment personalizzato per il trading con più criptovalute
class CryptoTradingEnv(gym.Env):
    def __init__(self, data):
        super(CryptoTradingEnv, self).__init__()
        self.data = data
        self.symbols = data['symbol'].unique()
        self.current_step = 0
        self.balance = 1000  # Capitale iniziale
        self.crypto_holdings = {symbol: 0 for symbol in self.symbols}
        self.total_value = self.balance
        self.commission = 0.0005  # Commissione ridotta allo 0.05%
        
        # Definizione degli spazi di azione e osservazione
        self.action_space = spaces.MultiDiscrete([3] * len(self.symbols))  # 0 = Hold, 1 = Buy, 2 = Sell per ciascuna crypto
        self.observation_space = spaces.Box(
            low=0, high=np.inf, shape=(len(self.symbols) * 4,), dtype=np.float32
        )

    def reset(self, seed=None):
        self.current_step = 0
        self.balance = 1000
        self.crypto_holdings = {symbol: 0 for symbol in self.symbols}
        self.total_value = self.balance
        return self._get_observation(), {}

    def _get_observation(self):
        obs = []
        for symbol in self.symbols:
            symbol_data = self.data[self.data['symbol'] == symbol]
            if self.current_step < len(symbol_data):
                step_data = symbol_data.iloc[self.current_step]
            else:
                step_data = symbol_data.iloc[-1]  # Usa l'ultimo valore disponibile se si supera il limite
            obs.extend([step_data['price'], step_data['high'], step_data['low'], step_data['volume']])
        return np.array(obs, dtype=np.float32)

    def step(self, actions):
        rewards = 0
        for i, symbol in enumerate(self.symbols):
            symbol_data = self.data[self.data['symbol'] == symbol]
            if self.current_step < len(symbol_data):
                current_price = symbol_data.iloc[self.current_step]['price']
            else:
                current_price = symbol_data.iloc[-1]['price']  # Usa l'ultimo prezzo disponibile se si supera il limite

            action = actions[i]
            
            # Azioni: 0 = Hold, 1 = Buy, 2 = Sell
            if action == 1 and self.balance >= current_price * (1 + self.commission):
                self.crypto_holdings[symbol] += 1
                self.balance -= current_price * (1 + self.commission)
            elif action == 2 and self.crypto_holdings[symbol] > 0:
                self.crypto_holdings[symbol] -= 1
                self.balance += current_price * (1 - self.commission)

        self.total_value = self.balance + sum(
            self.crypto_holdings[s] * self.data[self.data['symbol'] == s].iloc[min(self.current_step, len(self.data[self.data['symbol'] == s]) - 1)]['price']
            for s in self.symbols
        )

        self.current_step += 1
        done = self.current_step >= len(self.data) // len(self.symbols) - 1
        
        reward = (self.total_value - 1000) / 100  # Ricompensa basata sul profitto netto rispetto al capitale iniziale
        
        # Penalità per inattività
        if all(action == 0 for action in actions):
            reward -= 0.1
        
        return self._get_observation(), reward, done, False, {}

    def render(self):
        holdings_str = ', '.join([f"{symbol}: {self.crypto_holdings[symbol]}" for symbol in self.symbols])
        print(f"Step: {self.current_step}, Balance: {self.balance:.2f}, Holdings: {holdings_str}, Total Value: {self.total_value:.2f}")

# Funzione per addestrare l'agente con Q-Learning
def train_single_episode(env, q_table, alpha, gamma, epsilon):
    state, _ = env.reset()
    done = False
    
    while not done:
        if random.uniform(0, 1) < epsilon:
            actions = [env.action_space.sample()[i] for i in range(len(env.symbols))]
        else:
            actions = [np.argmax(q_table[env.current_step][i]) for i in range(len(env.symbols))]

        next_state, reward, done, _, _ = env.step(actions)

        for i in range(len(env.symbols)):
            q_table[env.current_step, i, actions[i]] += alpha * (
                reward + gamma * np.max(q_table[env.current_step, i]) - q_table[env.current_step, i, actions[i]]
            )

def train_agent(env, episodes=1000, alpha=0.1, gamma=0.99, epsilon=0.5):
    q_table = np.random.uniform(low=-1, high=1, size=(len(env.data) // len(env.symbols), len(env.symbols), env.action_space.nvec[0]))
    epsilon_decay = epsilon
    for episode in range(episodes):
        train_single_episode(env, q_table, alpha, gamma, epsilon_decay)
        epsilon_decay = max(0.01, epsilon_decay * 0.999)  # Decay più graduale
        if episode % 100 == 0:
            print(f"Completed Episode {episode}/{episodes}")
    return q_table

# Funzione per testare l'agente
def test_agent(env, q_table):
    state, _ = env.reset()
    done = False
    performance = []

    while not done:
        actions = [np.argmax(q_table[env.current_step][i]) for i in range(len(env.symbols))]
        state, reward, done, _, _ = env.step(actions)
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
        q_table = train_agent(env, episodes=1000)
        
        print("\n===== Inizio Testing =====")
        test_agent(env, q_table)
        
        print("\nTraining e Testing completati. Riinizio tra 10 secondi...\n")
        time.sleep(10)
