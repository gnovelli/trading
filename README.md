```markdown
# 📄 **Documentazione del Sistema di Trading Algoritmico**

## 1. **Introduzione**

Questo sistema è composto da due componenti principali:

1. **observer.py**: Un processo che osserva le quotazioni delle criptovalute tramite il WebSocket di Binance e registra i dati in tempo reale in un file di log.
2. **trader.py**: Un agente di Reinforcement Learning (RL) che utilizza i dati registrati per addestrare e testare una strategia di trading su più criptovalute contemporaneamente.

---

## 2. **observer.py**

### 📌 **Funzionalità**

- Connette al WebSocket di Binance per ricevere aggiornamenti sui prezzi di una lista di criptovalute.
- Registra i dati in tempo reale in un file di log con un formato JSON.
- Utilizza il logging per garantire scritture con flush immediato per evitare perdita di dati.

### ⚙️ **Criptovalute Monitorate**

- **Esempio di coppie osservate**:
  - `BTCUSDT`, `ETHUSDT`, `BNBUSDT`, `ADAUSDT`, `XRPUSDT`, `SOLUSDT`, `DOTUSDT`, `DOGEUSDT`, `MATICUSDT`, `LINKUSDT`

### 📝 **Formato dei Dati nel Log**

Ogni riga nel file di log contiene un oggetto JSON con il seguente formato:

```json
{
    "symbol": "BTCUSDT",
    "price": "99846.84000000",
    "high": "102540.00000000",
    "low": "99311.64000000",
    "volume": "30199.90165000"
}
```

### 🚀 **Avvio dell'Observer**

Eseguire il comando seguente per avviare il processo di osservazione:

```bash
python observer.py
```

Il file di log verrà salvato nella cartella `log/` come `crypto_price_log.log`.

---

## 3. **trader.py**

### 📌 **Funzionalità**

- Utilizza i dati dal file di log generato da **observer.py**.
- Implementa un ambiente personalizzato di trading con **Gymnasium**.
- Addestra un agente con l'algoritmo di **Q-Learning** per ottimizzare le decisioni di trading.
- Testa l'agente dopo l'addestramento per valutare la sua performance.

### ⚙️ **Componenti Principali**

#### 1. **Funzione `load_data`**

Carica i dati delle criptovalute dal file di log:

```python
data = load_data("log/crypto_price_log.log")
```

#### 2. **Classe `CryptoTradingEnv`**

Ambiente personalizzato per il trading con le seguenti caratteristiche:

- **Stato**: Prezzo corrente, massimo, minimo e volume di ciascuna criptovaluta.
- **Azioni**:
  - `0` = Hold (Mantenere la posizione)
  - `1` = Buy (Acquistare)
  - `2` = Sell (Vendere)
- **Ricompensa**: Basata sul profitto netto rispetto al capitale iniziale con una penalità per inattività.

#### 3. **Funzione `train_agent`**

Addestra l'agente per un numero specifico di episodi:

```python
q_table = train_agent(env, episodes=1000)
```

#### 4. **Funzione `test_agent`**

Testa l'agente utilizzando la Q-Table addestrata e visualizza le performance:

```python
test_agent(env, q_table)
```

#### 5. **Esecuzione del Training e Testing Continuo**

Il programma esegue cicli continui di training e testing:

```python
while True:
    print("\n===== Inizio Training =====")
    q_table = train_agent(env, episodes=1000)
    
    print("\n===== Inizio Testing =====")
    test_agent(env, q_table)
    
    print("\nTraining e Testing completati. Riinizio tra 10 secondi...\n")
    time.sleep(10)
```

### 📝 **Avvio del Trader**

Eseguire il comando seguente per avviare il processo di trading:

```bash
python trader.py
```

---

## 4. **Requisiti**

### 🐍 **Pacchetti Necessari**

Installare i pacchetti richiesti con:

```bash
pip install -r requirements.txt
```

### 📋 **requirements.txt**

```plaintext
websocket-client==1.2.1
gymnasium==0.26.3
numpy==1.23
pandas==1.3.3
matplotlib==3.4.3
joblib==1.0.1
```

---

## 5. **Note Aggiuntive**

- **Commissione di Trading**: È impostata allo **0.05%** per acquisti e vendite.
- **Penalità per Inattività**: Se l'agente non effettua operazioni (`Hold`), riceve una penalità per incentivare il trading attivo.
- **File di Log**: Assicurarsi che il file di log esista nella cartella `log/` prima di avviare `trader.py`.

---

## 6. **Esempio di Output**

### **observer.py** Output di Log

```
{"symbol": "BTCUSDT", "price": "99846.84000000", "high": "102540.00000000", "low": "99311.64000000", "volume": "30199.90165000"}
{"symbol": "ETHUSDT", "price": "3884.72000000", "high": "3987.41000000", "low": "3796.80000000", "volume": "557323.09640000"}
...
```

### **trader.py** Output Durante il Testing

```
Step: 1, Balance: 962.23, Holdings: ETHUSDT: 0, DOGEUSDT: 0, BNBUSDT: 0, SOLUSDT: 0, ADAUSDT: 0, DOTUSDT: 1, LINKUSDT: 1, BTCUSDT: 0, XRPUSDT: 0, Total Value: 999.96
Step: 2, Balance: 924.44, Holdings: ETHUSDT: 0, DOGEUSDT: 0, BNBUSDT: 0, SOLUSDT: 0, ADAUSDT: 0, DOTUSDT: 2, LINKUSDT: 2, BTCUSDT: 0, XRPUSDT: 0, Total Value: 999.93
...
```

---

## 🔗 **Conclusione**

Questo sistema fornisce una soluzione completa per osservare i dati di mercato in tempo reale e applicare strategie di trading algoritmico utilizzando l'apprendimento per rinforzo.
```
