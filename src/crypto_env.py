import gymnasium as gym
from gymnasium import spaces
from decimal import Decimal, getcontext
import numpy as np
import logging

# Imposta la precisione dei calcoli con Decimal
getcontext().prec = 10

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


# Definition of the cryptocurrency trading environment
class CryptoTradingEnv(gym.Env):
    def __init__(self, data, initial_balance=1000, commission=0.001, min_trade_amount=0.01, log_transactions=False):
        super(CryptoTradingEnv, self).__init__()
        
        # Initialization of environment parameters
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

        # Observation space: price, high, low, and volume for each cryptocurrency
        self.observation_space = spaces.Box(
            low=0, high=np.inf, shape=(len(self.symbols) * 4,), dtype=np.float32
        )

    # Method to reset the environment to its initial state
    def reset(self, seed=None):
        self.current_step = 0
        self.balance = self.initial_balance
        self.crypto_holdings = {symbol: 0 for symbol in self.symbols}
        self.total_value = self.balance
        return self._get_observation(), {}

    # Private method to get the current observation
    def _get_observation(self):
        obs = []
        for symbol in self.symbols:
            symbol_data = self.data[self.data['symbol'] == symbol]
            # Get data for the current step, if available
            if self.current_step < len(symbol_data):
                step_data = symbol_data.iloc[self.current_step]
            else:
                step_data = symbol_data.iloc[-1]  # Usa l'ultimo valore disponibile
            obs.extend([step_data['price'], step_data['high'], step_data['low'], step_data['volume']])
        return np.array(obs, dtype=np.float32)

    # Method to take a step in time with a set of actions
    def step(self, actions):
        rewards = 0
        for i, symbol in enumerate(self.symbols):
            symbol_data = self.data[self.data['symbol'] == symbol]
            # Get the current price of the symbol
            if self.current_step < len(symbol_data):
                current_price = Decimal(str(symbol_data.iloc[self.current_step]['price']))
            else:
                current_price = Decimal(str(symbol_data.iloc[-1]['price']))

            action = actions[i]

            # Azioni: 0 = Hold, 1 = Buy, 2 = Sell
            if action == 1 and self.balance >= current_price * (1 + self.commission):
                self.crypto_holdings[symbol] += 1
                self.balance -= current_price * (1 + self.commission)
            elif action == 2 and self.crypto_holdings[symbol] > 0:
                self.crypto_holdings[symbol] -= 1
                self.balance += current_price * (1 - self.commission)

        self.total_value = self.balance + sum(
            self.crypto_holdings[s] * Decimal(str(self.data[self.data['symbol'] == s].iloc[
                min(self.current_step, len(self.data[self.data['symbol'] == s]) - 1)
            ]['price']))
            for s in self.symbols
        )

        reward = float(self.total_value - previous_total_value)

        self.current_step += 1
        done = self.current_step >= len(self.data) // len(self.symbols) - 1

        reward = (self.total_value - self.initial_balance) / 100  # Ricompensa basata sul profitto netto

        # Return the next observation, reward, done flag, and additional info
        return self._get_observation(), reward, done, False, {}

    def render(self):
        print(f"Step: {self.current_step}, Balance: {self.balance:.2f}, Holdings: {self.crypto_holdings}, Total Value: {self.total_value:.2f}")
