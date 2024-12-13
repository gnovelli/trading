import numpy as np
import matplotlib.pyplot as plt

def train_agent(env, episodes=1000, alpha=0.1, gamma=0.99, epsilon=0.5):
    """
    Trains the agent using the Q-Learning algorithm.

    :param env: The trading environment.
    :param episodes: Number of training episodes.
    :param alpha: Learning rate.
    :param gamma: Discount factor for future rewards.
    :param epsilon: Initial exploration probability.
    :return: Trained Q-Table.
    """
    # Initialize Q-Table with random values between -1 and 1
    q_table = np.random.uniform(
        low=-1, 
        high=1, 
        size=(len(env.data) // len(env.symbols), len(env.symbols), env.action_space.nvec[0])
    )
    
    # Decay factor for epsilon to reduce exploration over time
    epsilon_decay = epsilon

    for episode in range(episodes):
        state, _ = env.reset()  # Reset environment at the start of each episode
        done = False

        while not done:
            actions = []
            # Choose actions for each symbol based on epsilon-greedy policy
            for i in range(len(env.symbols)):
                if np.random.uniform(0, 1) < epsilon_decay:
                    action = env.action_space.sample()[i]  # Explore: random action
                else:
                    action = np.argmax(q_table[env.current_step][i])  # Exploit: best-known action
                actions.append(action)

            # Take a step in the environment
            next_state, reward, done, _, _ = env.step(actions)

            # Update Q-Table using the Bellman equation
            for i in range(len(env.symbols)):
                q_table[env.current_step][i][actions[i]] += alpha * (
                    reward + gamma * np.max(q_table[env.current_step][i]) - q_table[env.current_step][i][actions[i]]
                )

        # Decay epsilon to reduce exploration over time, with a minimum threshold
        epsilon_decay = max(0.01, epsilon_decay * 0.999)

        # Print progress every 100 episodes
        if episode % 100 == 0:
            print(f"Completed Episode {episode}/{episodes}")

    return q_table

def test_agent(env, q_table):
    """
    Tests the agent using the trained Q-Table and visualizes performance.

    :param env: The trading environment.
    :param q_table: The trained Q-Table.
    """
    state, _ = env.reset()  # Reset environment before testing
    done = False
    performance = []  # List to track total portfolio value at each step

    while not done:
        # Select the best action for each symbol based on the Q-Table
        actions = [np.argmax(q_table[env.current_step][i]) for i in range(len(env.symbols))]
        state, reward, done, _, _ = env.step(actions)
        performance.append(env.total_value)  # Record the total portfolio value
        env.render()  # Print the current state of the environment

    # Plot the performance after testing
    plot_performance(performance)

def plot_performance(performance):
    """
    Plots the agent's performance during testing.

    :param performance: List of total portfolio values at each step.
    """
    plt.plot(performance)  # Plot the performance values over time
    plt.xlabel('Step')     # Label for the x-axis
    plt.ylabel('Total Value')  # Label for the y-axis
    plt.title('Trading Performance')  # Title of the plot
    plt.show()  # Display the plot
