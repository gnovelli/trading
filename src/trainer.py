import numpy as np
import matplotlib.pyplot as plt

def train_agent(env, episodes=1000, alpha=0.1, gamma=0.99, epsilon=0.5):
    """
    Addestra l'agente utilizzando l'algoritmo Q-Learning.

    :param env: L'ambiente di trading.
    :param episodes: Numero di episodi di training.
    :param alpha: Tasso di apprendimento.
    :param gamma: Fattore di sconto per le ricompense future.
    :param epsilon: Probabilità di esplorazione iniziale.
    :return: Q-Table addestrata.
    """
    q_table = np.random.uniform(low=-1, high=1, size=(len(env.data) // len(env.symbols), len(env.symbols), env.action_space.nvec[0]))
    epsilon_decay = epsilon

    for episode in range(episodes):
        state, _ = env.reset()
        done = False

        while not done:
            actions = []
            for i in range(len(env.symbols)):
                if np.random.uniform(0, 1) < epsilon_decay:
                    action = env.action_space.sample()[i]
                else:
                    action = np.argmax(q_table[env.current_step][i])
                actions.append(action)

            next_state, reward, done, _, _ = env.step(actions)

            # Aggiornamento della Q-Table
            for i in range(len(env.symbols)):
                q_table[env.current_step][i][actions[i]] += alpha * (
                    reward + gamma * np.max(q_table[env.current_step][i]) - q_table[env.current_step][i][actions[i]]
                )

        epsilon_decay = max(0.01, epsilon_decay * 0.999)

        if episode % 100 == 0:
            print(f"Completed Episode {episode}/{episodes}")

    return q_table

def test_agent(env, q_table):
    """
    Testa l'agente utilizzando la Q-Table addestrata e visualizza le performance.

    :param env: L'ambiente di trading.
    :param q_table: La Q-Table addestrata.
    """
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
    """
    Visualizza un grafico delle performance dell'agente durante il testing.

    :param performance: Lista dei valori totali del portafoglio a ogni step.
    """
    plt.plot(performance)
    plt.xlabel('Step')
    plt.ylabel('Total Value')
    plt.title('Trading Performance')
    plt.show()