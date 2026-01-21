# src/logic.py
import yfinance as yf
import pandas as pd
import requests

def analizza_titoli_dinamico():
    """Recupera l'S&P 500, analizza e restituisce i 20 migliori titoli."""
    try:
        # Recupero ticker (usa lxml o html5lib installati via requirements.txt)
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        df_sp = pd.read_html(url)[0]
        tickers = df_sp['Symbol'].tolist()
    except Exception:
        # Fallback di emergenza se Wikipedia non risponde
        tickers = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B"]

    risultati = []
    # Analizziamo un campione (es. primi 70) per velocità e stabilità
    pool = tickers[:70] 

    for ticker in pool:
        try:
            symbol = ticker.replace('.', '-')
            t = yf.Ticker(symbol)
            hist = t.history(period="2y") # Ridotto a 2 anni per velocità
            
            if hist.empty or len(hist) < 20: continue
            
            info = t.info
            curr_p = info.get('currentPrice') or hist['Close'].iloc[-1]
            target = info.get('targetMeanPrice')
            
            # Calcolo Crescite (Gestione sicura degli errori di data)
            c24 = 0.0
            h24 = hist[hist.index.year == 2024]
            if not h24.empty:
                c24 = ((h24['Close'].iloc[-1] / h24['Close'].iloc[0]) - 1) * 100
            
            # Sentiment & Trend
            sma200 = hist['Close'].rolling(window=200).mean().iloc[-1] if len(hist) > 200 else curr_p
            trend = "🚀 Rialzista" if curr_p > sma200 else "⚖️ Laterale"
            
            # Score per il ranking
            score = 0
            if curr_p > sma200: score += 50
            if target and target > curr_p: score += 50

            risultati.append({
                "Codice": symbol,
                "Azienda": info.get('longName', symbol),
                "Settore": info.get('sector', 'N/A'),
                "Crescita 2024 (%)": round(c24, 2),
                "Trend di Mercato": trend,
                "Score": score,
                "TradingView": f"https://www.tradingview.com/symbols/{symbol}/"
            })
        except:
            continue
            
    if not risultati:
        return pd.DataFrame()

    df_final = pd.DataFrame(risultati)
    return df_final.sort_values(by="Score", ascending=False).head(20)
