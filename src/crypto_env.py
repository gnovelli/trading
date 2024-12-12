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

        # Spazio delle azioni: [Hold, Buy, Sell] per ogni criptovaluta
        self.action_space = spaces.MultiDiscrete([3] * len(self.symbols))

        # Spazio delle osservazioni: prezzo, massimo, minimo e volume per ciascuna criptovaluta
        self.observation_space = spaces.Box(
            low=0, high=np.inf, shape=(len(self.symbols) * 4,), dtype=np.float32
        )

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
                step_data = symbol_data.iloc[-1]  # Usa l'ultimo valore disponibile
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

            # Azioni: 0 = Hold, 1 = Buy, 2 = Sell
            if action == 1 and self.balance >= current_price * (1 + self.commission):
                self.crypto_holdings[symbol] += 1
                self.balance -= current_price * (1 + self.commission)
            elif action == 2 and self.crypto_holdings[symbol] > 0:
                self.crypto_holdings[symbol] -= 1
                self.balance += current_price * (1 - self.commission)

        self.total_value = self.balance + sum(
            self.crypto_holdings[s] * self.data[self.data['symbol'] == s].iloc[
                min(self.current_step, len(self.data[self.data['symbol'] == s]) - 1)
            ]['price']
            for s in self.symbols
        )

        self.current_step += 1
        done = self.current_step >= len(self.data) // len(self.symbols) - 1

        reward = (self.total_value - self.initial_balance) / 100  # Ricompensa basata sul profitto netto

        return self._get_observation(), reward, done, False, {}

    def render(self):
        print(f"Step: {self.current_step}, Balance: {self.balance:.2f}, Holdings: {self.crypto_holdings}, Total Value: {self.total_value:.2f}")
