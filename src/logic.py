# src/logic.py
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

def get_sp500_tickers():
    """Recupera la lista aggiornata dei ticker S&P 500"""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        df = pd.read_html(url)[0]
        return df['Symbol'].tolist()
    except:
        return ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA"]

def analizza_titoli_dinamico(pool_size=80):
    """Esegue l'analisi quantitativa e qualitativa"""
    all_tickers = get_sp500_tickers()
    pool = all_tickers[:pool_size]
    risultati = []
    
    for ticker in pool:
        try:
            symbol = ticker.replace('.', '-')
            t = yf.Ticker(symbol)
            hist = t.history(period="3y") # 3 anni per avere dati puliti sugli ultimi 2
            
            if hist.empty or len(hist) < 500: continue
            
            info = t.info
            # Calcolo Crescite % (Ultimi 2 anni solari)
            # 2024
            h24 = hist[hist.index.year == 2024]
            c24 = ((h24['Close'].iloc[-1] / h24['Close'].iloc[0]) - 1) * 100 if not h24.empty else 0
            # 2025
            h25 = hist[hist.index.year == 2025]
            c25 = ((h25['Close'].iloc[-1] / h25['Close'].iloc[0]) - 1) * 100 if not h25.empty else 0
            
            # Sentiment Score (Basato su Momentum e Target Analisti)
            curr_p = info.get('currentPrice', hist['Close'].iloc[-1])
            target = info.get('targetMeanPrice', curr_p)
            upside = ((target / curr_p) - 1) * 100
            
            # Trend di Mercato (Prezzo vs Media Mobile 200 giorni)
            sma200 = hist['Close'].rolling(window=200).mean().iloc[-1]
            trend = "🚀 Rialzista" if curr_p > sma200 else "⚖️ Laterale/Debole"
            
            # Calcolo punteggio sentiment per ranking
            score = 0
            if curr_p > sma200: score += 50
            if upside > 10: score += 50
            
            risultati.append({
                "Codice": symbol,
                "Azienda": info.get('longName', symbol),
                "Settore": info.get('sector', 'N/A'),
                "Crescita 2024 (%)": round(c24, 2),
                "Crescita 2025 (%)": round(c25, 2),
                "Trend di Mercato": trend,
                "Sentiment": "🔥 Eccellente" if score == 100 else "📈 Positivo",
                "Score": score,
                "TradingView": f"https://www.tradingview.com/symbols/{symbol}/"
            })
        except:
            continue
            
    # Restituisce i primi 20 per sentiment score
    df = pd.DataFrame(risultati)
    return df.sort_values(by="Score", ascending=False).head(20)
