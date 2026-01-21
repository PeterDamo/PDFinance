import yfinance as yf
import pandas as pd
import requests

def get_market_tickers():
    """Recupera ticker da S&P 500, NASDAQ-100 ed ETF."""
    tickers = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # S&P 500
        df_sp = pd.read_html(requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", headers=headers).text)[0]
        tickers.extend(df_sp['Symbol'].tolist())
        # NASDAQ-100
        df_nd = pd.read_html(requests.get("https://en.wikipedia.org/wiki/Nasdaq-100", headers=headers).text)[4]
        tickers.extend(df_nd['Ticker'].tolist())
    except: pass
    
    # ETF Leader strategici
    etfs = ["SPY", "QQQ", "DIA", "IWM", "VGT", "SCHD", "VIG", "GLD", "IBIT"]
    tickers.extend(etfs)
    return list(set(tickers))

def analizza_mercato_completo():
    """Analizza il mercato e restituisce i 30 migliori asset."""
    all_tickers = get_market_tickers()
    risultati = []
    # Analisi su un pool ampio per estrarre i 30 migliori
    pool = all_tickers[:550]

    for ticker in pool:
        try:
            symbol = str(ticker).replace('.', '-')
            t = yf.Ticker(symbol)
            hist = t.history(period="3y")
            if hist.empty: continue
            
            info = t.info
            curr_p = info.get('currentPrice') or hist['Close'].iloc[-1]
            
            # --- GESTIONE DIVIDENDO (Divisione per 100) ---
            div_raw = info.get('dividendYield') or info.get('trailingAnnualDividendYield') or 0
            if div_raw is None: div_raw = 0
            # Dividiamo per 100 per ottenere il decimale corretto (es. 0.035)
            div_val = float(div_raw) / 100 
            
            # Performance 2024 e 2025
            h24 = hist[hist.index.year == 2024]
            p24 = ((h24['Close'].iloc[-1] / h24['Close'].iloc[0]) - 1) * 100 if not h24.empty else 0
            h25 = hist[hist.index.year == 2025]
            p25 = ((h25['Close'].iloc[-1] / h25['Close'].iloc[0]) - 1) * 100 if not h25.empty else 0
            
            # Previsione 2026
            target = info.get('targetMeanPrice')
            prev_2026 = ((target / curr_p) - 1) * 100 if target else p25 * 0.7
            
            # Buy Score (0-100)
            score = 0
            sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            if curr_p > sma50: score += 30
            if prev_2026 > 10: score += 40
            if 'buy' in str(info.get('recommendationKey', '')).lower() or not target: score += 30

            risultati.append({
                "Codice": symbol,
                "Nome": info.get('longName', symbol),
                "Tipo": "ETF" if info.get('quoteType') == 'ETF' else "Azione",
                "Settore": info.get('sector') or info.get('category', 'N/A'),
                "Dividendo (%)": round(div_val, 4), # Decimale per main.py
                "Perf. 2024 (%)": round(p24, 2),
                "Perf. 2025 (%)": round(p25, 2),
                "Previsione 2026 (%)": round(prev_2026, 2),
                "Buy Score": score,
                "TradingView": f"https://www.tradingview.com/symbols/{symbol}/"
            })
        except: continue
            
    df_final = pd.DataFrame(risultati)
    return df_final.sort_values(by="Buy Score", ascending=False).head(30)
