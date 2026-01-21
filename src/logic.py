# src/logic.py
import yfinance as yf
import pandas as pd
import requests

def get_sp500_tickers():
    """Recupera la lista ufficiale dei 500 titoli S&P 500."""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        df_sp = pd.read_html(response.text)[0]
        return df_sp['Symbol'].tolist()
    except Exception:
        return []

def analizza_titoli_dinamico():
    """Scansiona i 500 titoli e calcola performance storiche e Score."""
    tickers = get_sp500_tickers()
    if not tickers:
        return pd.DataFrame()

    risultati = []
    # Analizziamo l'indice (limitiamo a un pool per stabilità su Streamlit Cloud se necessario)
    pool = tickers[:500] 

    for ticker in pool:
        try:
            symbol = ticker.replace('.', '-')
            t = yf.Ticker(symbol)
            # Recuperiamo 3 anni di dati per coprire 2024, 2025 e inizio 2026
            hist = t.history(period="3y")
            if hist.empty or len(hist) < 100: continue
            
            info = t.info
            curr_p = info.get('currentPrice') or hist['Close'].iloc[-1]
            target = info.get('targetMeanPrice')
            
            # --- 1. Andamento Anno-2 (2024) ---
            h24 = hist[hist.index.year == 2024]
            perf_24 = ((h24['Close'].iloc[-1] / h24['Close'].iloc[0]) - 1) * 100 if not h24.empty else 0
            
            # --- 2. Andamento Anno-1 (2025) ---
            h25 = hist[hist.index.year == 2025]
            perf_25 = ((h25['Close'].iloc[-1] / h25['Close'].iloc[0]) - 1) * 100 if not h25.empty else 0
            
            # --- 3. Calcolo Score (0-100) ---
            score = 0
            # Componente Tecnica (Trend): Prezzo sopra media mobile 50gg
            sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            if curr_p > sma50: score += 30
            
            # Componente Analisti (Potenziale): Upside vs Target
            if target:
                upside = ((target / curr_p) - 1) * 100
                if upside > 15: score += 40
                elif upside > 0: score += 20
            
            # Componente Consenso: Rating Yahoo Finance
            rec = str(info.get('recommendationKey', '')).lower()
            if 'strong_buy' in rec: score += 30
            elif 'buy' in rec: score += 20

            risultati.append({
                "Codice": symbol,
                "Azienda": info.get('longName', symbol),
                "Settore": info.get('sector', 'N/A'),
                "Andamento 2024 (%)": round(perf_24, 2),
                "Andamento 2025 (%)": round(perf_25, 2),
                "Trend di Mercato": "🚀 Rialzista" if curr_p > sma50 else "⚖️ Laterale",
                "Buy Score": score,
                "TradingView": f"https://www.tradingview.com/symbols/{symbol}/"
            })
        except:
            continue
            
    if not risultati:
        return pd.DataFrame()

    df_final = pd.DataFrame(risultati)
    # Ritorna i primi 20 titoli con il Buy Score più alto
    return df_final.sort_values(by="Buy Score", ascending=False).head(20)
