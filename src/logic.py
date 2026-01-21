# src/logic.py
import yfinance as yf
import pandas as pd
import requests

def get_sp500_tickers():
    """Recupera la lista completa di 500 titoli da Wikipedia."""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        # Utilizziamo headers per evitare blocchi
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        df_sp = pd.read_html(response.text)[0]
        return df_sp['Symbol'].tolist()
    except Exception:
        return []

def analizza_titoli_dinamico():
    """Scansiona i 500 titoli e restituisce i 20 migliori."""
    tickers = get_sp500_tickers()
    
    if not tickers:
        return pd.DataFrame() # Ritorna vuoto se non trova ticker

    risultati = []
    
    # Per una scansione reale di 500 titoli servirebbe tempo, 
    # qui implementiamo la logica su tutto l'elenco ricevuto.
    for ticker in tickers:
        try:
            symbol = ticker.replace('.', '-')
            t = yf.Ticker(symbol)
            # Usiamo un periodo breve (1 anno) per velocizzare la scansione di 500 titoli
            hist = t.history(period="1y")
            
            if hist.empty or len(hist) < 20:
                continue
            
            info = t.info
            curr_p = info.get('currentPrice') or hist['Close'].iloc[-1]
            target = info.get('targetMeanPrice')
            
            # Calcolo Crescite (Esempio su base disponibile)
            c_year = ((hist['Close'].iloc[-1] / hist['Close'].iloc[0]) - 1) * 100
            
            # Sentiment e Trend
            sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            trend = "🚀 Rialzista" if curr_p > sma50 else "⚖️ Laterale"
            
            # Score per il ranking (Sentiment)
            score = 0
            if curr_p > sma50: score += 50
            if target and target > curr_p: score += 50

            # Solo titoli con sentiment positivo entrano nel pool
            if score > 0:
                risultati.append({
                    "Codice": symbol,
                    "Azienda": info.get('longName', symbol),
                    "Settore": info.get('sector', 'N/A'),
                    "Crescita (%)": round(c_year, 2),
                    "Trend di Mercato": trend,
                    "Score": score,
                    "TradingView": f"https://www.tradingview.com/symbols/{symbol}/"
                })
        except:
            continue
            
    if not risultati:
        return pd.DataFrame()

    df_final = pd.DataFrame(risultati)
    # Ritorna i primi 20 migliori dopo aver scansionato tutto
    return df_final.sort_values(by="Score", ascending=False).head(20)
