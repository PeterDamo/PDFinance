# src/logic.py
import yfinance as yf
import pandas as pd

def calcola_sentiment_dinamico(tickers):
    """Logica pura di analisi. Se vuoi cambiare i pesi del sentiment, 
    modifichi solo queste righe."""
    risultati = []
    for t in tickers:
        # Immagina qui tutta la logica di analisi...
        score = 85 # Esempio
        risultati.append({"Ticker": t, "Score": score})
    return pd.DataFrame(risultati)

def prepara_download_csv(df):
    """Trasforma il dataframe in CSV pronto per il download."""
    return df.to_csv(index=False).encode('utf-8')
