
# 📄 Documentazione del Sistema di Trading Algoritmico

## 1. **Introduzione**

Questo sistema è composto da cinque componenti principali:

1. **observer.py**: Osserva le quotazioni delle criptovalute in tempo reale tramite il WebSocket di Binance e registra i dati in un file di log.
2. **data_manager.py**: Carica e pre-processa i dati dal file di log.
3. **crypto_env.py**: Definisce l'ambiente di trading personalizzato utilizzato dall'agente.
4. **trainer.py**: Contiene le funzioni per l'addestramento e il testing dell'agente di Reinforcement Learning.
5. **trader.py**: Coordina l'addestramento e il testing continuo dell'agente.

---

## 📂 **Struttura dei File**

```
project/
│-- observer.py
│-- data_manager.py
│-- crypto_env.py
│-- trainer.py
│-- trader.py
│-- log/
│   └── crypto_price_log.log
└-- requirements.txt
```

---

## 2. **observer.py**

### 📌 **Funzionalità**

- Connettersi al WebSocket di Binance per ricevere i dati in tempo reale.
- Registrare i dati delle criptovalute in un file di log con un formato JSON.
- Utilizzare il logging per garantire scritture con flush immediato.

### 📝 **Esempio di Log Generato**

```json
{"symbol": "BTCUSDT", "price": "99846.84000000", "high": "102540.00000000", "low": "99311.64000000", "volume": "30199.90165000"}
```

### 🚀 **Esecuzione**

```bash
python observer.py
```

---

## 3. **data_manager.py**

### 📌 **Funzionalità**

- Caricare i dati dal file di log generato da `observer.py`.
- Gestire eventuali errori durante la lettura dei dati.

### 📝 **Esempio di Codice**

```python
import pandas as pd
import json

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
                print(f"Errore durante il caricamento dei dati: {e}")
    return pd.DataFrame(data)
```

---

## 4. **crypto_env.py**

### 📌 **Funzionalità**

- Ambiente personalizzato per il trading basato su Gymnasium.
- Supporta operazioni di acquisto, vendita e mantenimento delle criptovalute.

### 📝 **Esempio di Codice**

```python
import gymnasium as gym
from gymnasium import spaces
import numpy as np

class CryptoTradingEnv(gym.Env):
    def __init__(self, data, initial_balance=1000, commission=0.0005):
        super(CryptoTradingEnv, self).__init__()
        self.data = data
        self.symbols = data['symbol'].unique()
        self.current_step = 0
        self.initial_balance = initial_balance
        self.balance = initial_balance
        self.commission = commission
        self.crypto_holdings = {symbol: 0 for symbol in self.symbols}
        self.total_value = self.balance

        self.action_space = spaces.MultiDiscrete([3] * len(self.symbols))
        self.observation_space = spaces.Box(low=0, high=np.inf, shape=(len(self.symbols) * 4,), dtype=np.float32)

    def reset(self, seed=None):
        self.current_step = 0
        self.balance = self.initial_balance
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
                step_data = symbol_data.iloc[-1]
            obs.extend([step_data['price'], step_data['high'], step_data['low'], step_data['volume']])
        return np.array(obs, dtype=np.float32)

    def step(self, actions):
        rewards = 0
        for i, symbol in enumerate(self.symbols):
            symbol_data = self.data[self.data['symbol'] == symbol]
            if self.current_step < len(symbol_data):
                current_price = symbol_data.iloc[self.current_step]['price']
            else:
                current_price = symbol_data.iloc[-1]['price']

            action = actions[i]
            if action == 1 and self.balance >= current_price * (1 + self.commission):
                self.crypto_holdings[symbol] += 1
                self.balance -= current_price * (1 + self.commission)
            elif action == 2 and self.crypto_holdings[symbol] > 0:
                self.crypto_holdings[symbol] -= 1
                self.balance += current_price * (1 - self.commission)

        self.total_value = self.balance + sum(self.crypto_holdings[symbol] * symbol_data.iloc[min(self.current_step, len(symbol_data)-1)]['price'] for symbol in self.symbols)
        self.current_step += 1
        done = self.current_step >= len(self.data) // len(self.symbols) - 1
        reward = (self.total_value - self.initial_balance) / 100

        return self._get_observation(), reward, done, False, {}

    def render(self):
        print(f"Step: {self.current_step}, Balance: {self.balance:.2f}, Holdings: {self.crypto_holdings}, Total Value: {self.total_value:.2f}")
```

---

## 5. **trainer.py**

### 📌 **Funzionalità**

- Funzioni per l'addestramento e il testing dell'agente.

### 📝 **Esempio di Codice**

```python
import numpy as np
import matplotlib.pyplot as plt

def train_agent(env, episodes=1000, alpha=0.1, gamma=0.99, epsilon=0.5):
    q_table = np.random.uniform(low=-1, high=1, size=(len(env.data) // len(env.symbols), len(env.symbols), env.action_space.nvec[0]))
    epsilon_decay = epsilon
    for episode in range(episodes):
        train_single_episode(env, q_table, alpha, gamma, epsilon_decay)
        epsilon_decay = max(0.01, epsilon_decay * 0.999)
        if episode % 100 == 0:
            print(f"Completed Episode {episode}/{episodes}")
    return q_table

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
```

---

## 📥 **Download del File**

Puoi scaricare il file completo [qui](project_documentation.md).
