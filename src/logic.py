# src/logic.py
import yfinance as yf
import pandas as pd
import requests

def get_sp500_tickers():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        df_sp = pd.read_html(response.text)[0]
        return df_sp['Symbol'].tolist()
    except Exception:
        return []

def analizza_titoli_dinamico():
    tickers = get_sp500_tickers()
    if not tickers: return pd.DataFrame()

    risultati = []
    pool = tickers[:500] 

    for ticker in pool:
        try:
            symbol = ticker.replace('.', '-')
            t = yf.Ticker(symbol)
            hist = t.history(period="3y")
            if hist.empty: continue
            
            info = t.info
            curr_p = info.get('currentPrice') or hist['Close'].iloc[-1]
            target = info.get('targetMeanPrice')
            
            # --- Calcolo Dividendo ---
            div_yield = info.get('dividendYield', 0)
            if div_yield is None: div_yield = 0
            div_perc = div_yield * 100 # Converte in percentuale
            
            # --- Performance Storiche ---
            h24 = hist[hist.index.year == 2024]
            perf_24 = ((h24['Close'].iloc[-1] / h24['Close'].iloc[0]) - 1) * 100 if not h24.empty else 0
            h25 = hist[hist.index.year == 2025]
            perf_25 = ((h25['Close'].iloc[-1] / h25['Close'].iloc[0]) - 1) * 100 if not h25.empty else 0
            
            # --- Previsione 2026 ---
            prev_2026 = ((target / curr_p) - 1) * 100 if target else 0.0
            
            # --- Score (0-100) ---
            score = 0
            sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            if curr_p > sma50: score += 30
            if prev_2026 > 15: score += 40
            elif prev_2026 > 0: score += 20
            if 'buy' in str(info.get('recommendationKey', '')).lower(): score += 30

            risultati.append({
                "Codice": symbol,
                "Azienda": info.get('longName', symbol),
                "Settore": info.get('sector', 'N/A'),
                "Dividendo (%)": round(div_perc, 2), # Nuova Colonna
                "Andamento 2024 (%)": round(perf_24, 2),
                "Andamento 2025 (%)": round(perf_25, 2),
                "Previsione 2026 (%)": round(prev_2026, 2),
                "Buy Score": score,
                "TradingView": f"https://www.tradingview.com/symbols/{symbol}/"
            })
        except:
            continue
            
    df_final = pd.DataFrame(risultati)
    return df_final.sort_values(by="Buy Score", ascending=False).head(20)
