import gymnasium as gym
from gymnasium import spaces
from decimal import Decimal, getcontext
import numpy as np
import logging

# Imposta la precisione dei calcoli con Decimal
getcontext().prec = 10

# Configurazione del logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


class CryptoTradingEnv(gym.Env):
    def __init__(self, data, initial_balance=1000, commission=0.001, min_trade_amount=0.01, log_transactions=False):
        super(CryptoTradingEnv, self).__init__()
        self.data = data
        self.symbols = data['symbol'].unique()
        self.current_step = 0
        self.initial_balance = Decimal(str(initial_balance))
        self.balance = self.initial_balance
        self.commission = Decimal(str(commission))
        self.min_trade_amount = Decimal(str(min_trade_amount))
        self.crypto_holdings = {symbol: Decimal('0.0') for symbol in self.symbols}
        self.total_value = self.balance
        self.log_transactions = log_transactions

        # Spazio delle azioni: [Hold, Buy, Sell] per ogni criptovaluta
        self.action_space = spaces.MultiDiscrete([3] * len(self.symbols))

        # Spazio delle osservazioni: prezzo, massimo, minimo e volume per ciascuna criptovaluta
        self.observation_space = spaces.Box(
            low=0, high=np.inf, shape=(len(self.symbols) * 4,), dtype=np.float32
        )

    def reset(self, seed=None):
        self.current_step = 0
        self.balance = self.initial_balance
        self.crypto_holdings = {symbol: Decimal('0.0') for symbol in self.symbols}
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
        previous_total_value = self.total_value

        for i, symbol in enumerate(self.symbols):
            symbol_data = self.data[self.data['symbol'] == symbol]
            if self.current_step < len(symbol_data):
                current_price = Decimal(str(symbol_data.iloc[self.current_step]['price']))
            else:
                current_price = Decimal(str(symbol_data.iloc[-1]['price']))

            action = actions[i]

            # Azioni: 0 = Hold, 1 = Buy, 2 = Sell
            if action == 1 and self.balance >= current_price * self.min_trade_amount * (1 + self.commission):
                amount = self.min_trade_amount
                self.crypto_holdings[symbol] += amount
                cost = current_price * amount * (1 + self.commission)
                self.balance -= cost
                self._log_transaction(f"Acquistato {amount} di {symbol} al prezzo {current_price}")

            elif action == 2 and self.crypto_holdings[symbol] >= self.min_trade_amount:
                amount = self.min_trade_amount
                self.crypto_holdings[symbol] -= amount
                revenue = current_price * amount * (1 - self.commission)
                self.balance += revenue
                self._log_transaction(f"Venduto {amount} di {symbol} al prezzo {current_price}")

        # Calcola il nuovo valore totale del portafoglio
        self.total_value = self.balance + sum(
            self.crypto_holdings[s] * Decimal(str(self.data[self.data['symbol'] == s].iloc[
                min(self.current_step, len(self.data[self.data['symbol'] == s]) - 1)
            ]['price']))
            for s in self.symbols
        )

        reward = float(self.total_value - previous_total_value)

        self.current_step += 1
        done = self.current_step >= len(self.data) // len(self.symbols) - 1

        return self._get_observation(), reward, done, False, {}

    def _log_transaction(self, message):
        if self.log_transactions:
            logging.info(f"{message} | Valore totale portafoglio: {self.total_value:.2f}")

    def render(self):
        print(f"Step: {self.current_step}, Balance: {self.balance:.2f}, Holdings: {self.crypto_holdings}, Total Value: {self.total_value:.2f}")
