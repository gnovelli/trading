import gymnasium as gym
from gymnasium import spaces
import numpy as np

# Definition of the cryptocurrency trading environment
class CryptoTradingEnv(gym.Env):
    def __init__(self, data, initial_balance=1000, commission=0.0005):
        super(CryptoTradingEnv, self).__init__()
        
        # Initialization of environment parameters
        self.data = data
        self.symbols = data['symbol'].unique()  # List of unique cryptocurrency symbols
        self.current_step = 0  # Current step in the simulation
        self.initial_balance = initial_balance  # Initial balance of the agent
        self.balance = initial_balance  # Current balance of the agent
        self.commission = commission  # Transaction fee
        self.crypto_holdings = {symbol: 0 for symbol in self.symbols}  # Amount of each cryptocurrency held
        self.total_value = self.balance  # Total portfolio value (balance + value of held cryptocurrencies)

        # Action space: [Hold, Buy, Sell] for each cryptocurrency
        self.action_space = spaces.MultiDiscrete([3] * len(self.symbols))

        # Observation space: price, high, low, and volume for each cryptocurrency
        self.observation_space = spaces.Box(
            low=0, high=np.inf, shape=(len(self.symbols) * 4,), dtype=np.float32
        )

    # Method to reset the environment to its initial state
    def reset(self, seed=None):
        self.current_step = 0  # Reset current step to 0
        self.balance = self.initial_balance  # Reset balance to initial value
        self.crypto_holdings = {symbol: 0 for symbol in self.symbols}  # Reset held cryptocurrencies
        self.total_value = self.balance  # Reset total value to initial balance
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
                step_data = symbol_data.iloc[-1]  # Use the last available value if beyond the dataset
            # Add price, high, low, and volume to the observation
            obs.extend([step_data['price'], step_data['high'], step_data['low'], step_data['volume']])
        return np.array(obs, dtype=np.float32)

    # Method to take a step in time with a set of actions
    def step(self, actions):
        rewards = 0  # Initialize reward to zero
        for i, symbol in enumerate(self.symbols):
            symbol_data = self.data[self.data['symbol'] == symbol]
            # Get the current price of the symbol
            if self.current_step < len(symbol_data):
                current_price = symbol_data.iloc[self.current_step]['price']
            else:
                current_price = symbol_data.iloc[-1]['price']

            action = actions[i]

            # Actions: 0 = Hold, 1 = Buy, 2 = Sell
            if action == 1 and self.balance >= current_price * (1 + self.commission):
                # Buy one unit of the cryptocurrency
                self.crypto_holdings[symbol] += 1
                self.balance -= current_price * (1 + self.commission)  # Deduct cost with commission
            elif action == 2 and self.crypto_holdings[symbol] > 0:
                # Sell one unit of the cryptocurrency
                self.crypto_holdings[symbol] -= 1
                self.balance += current_price * (1 - self.commission)  # Add profit with commission

        # Calculate the total portfolio value (balance + value of held cryptocurrencies)
        self.total_value = self.balance + sum(
            self.crypto_holdings[s] * self.data[self.data['symbol'] == s].iloc[
                min(self.current_step, len(self.data[self.data['symbol'] == s]) - 1)
            ]['price']
            for s in self.symbols
        )

        self.current_step += 1  # Advance one step in the simulation
        done = self.current_step >= len(self.data) // len(self.symbols) - 1  # End episode if at dataset end

        # Reward based on net profit
        reward = (self.total_value - self.initial_balance) / 100

        # Return the next observation, reward, done flag, and additional info
        return self._get_observation(), reward, done, False, {}

    # Method to display the current state of the environment
    def render(self):
        print(f"Step: {self.current_step}, Balance: {self.balance:.2f}, Holdings: {self.crypto_holdings}, Total Value: {self.total_value:.2f}")
