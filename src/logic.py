# src/logic.py
import yfinance as yf
import pandas as pd
import requests

def get_market_tickers():
    """Recupera ticker da S&P 500, NASDAQ-100 e una selezione di ETF leader."""
    tickers = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. S&P 500
    try:
        url_sp = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        df_sp = pd.read_html(requests.get(url_sp, headers=headers).text)[0]
        tickers.extend(df_sp['Symbol'].tolist())
    except: pass

    # 2. NASDAQ-100
    try:
        url_nasdaq = "https://en.wikipedia.org/wiki/Nasdaq-100"
        # Spesso è la 3a o 4a tabella nella pagina
        df_nasdaq = pd.read_html(requests.get(url_nasdaq, headers=headers).text)[4]
        tickers.extend(df_nasdaq['Ticker'].tolist())
    except: pass

    # 3. Selezione ETF Strategici (Mercato, Tech, Dividendi, Oro, Crypto)
    etfs = ["SPY", "QQQ", "DIA", "IWM", "VTI", "VOO", "VGT", "SCHD", "VIG", "GLD", "IBIT"]
    tickers.extend(etfs)
    
    return list(set(tickers)) # Rimuove duplicati

def analizza_mercato_completo():
    """Analizza Azioni + ETF e restituisce i migliori 30 oggetti."""
    all_tickers = get_market_tickers()
    if not all_tickers: return pd.DataFrame()

    risultati = []
    # Analizziamo un pool ampio per trovare i 30 migliori
    pool = all_tickers[:600] 

    for ticker in pool:

        info = t.info
            
            # Recupero del dividendo (gestisce diverse chiavi di yfinance)
            div_raw = info.get('dividendYield') or info.get('trailingAnnualDividendYield') or 0
            
            # Se div_raw è None lo forziamo a 0
            if div_raw is None: div_raw = 0
            
            # CONVERSIONE IN PERCENTUALE ESPLICITA
            div_perc = float(div_raw) * 100 
            
# ... nell'assegnazione al dizionario risultati ...
            risultati.append({
                "Codice": symbol,
                "Nome": info.get('longName', symbol),
                "Tipo": "ETF" if info.get('quoteType') == 'ETF' else "Azione",
                "Settore/Asset": info.get('sector') or info.get('category', 'N/A'),
                "Dividendo (%)": round(div_perc, 2), # Salviamo es. 3.50
                "Perf. 2024 (%)": round(perf_24, 2),
                "Perf. 2025 (%)": round(perf_25, 2),
                "Previsione 2026 (%)": round(prev_2026, 2),
                "Buy Score": score,
                "TradingView": f"https://www.tradingview.com/symbols/{symbol}/"
            })
        
    
        except: continue
            
    df_final = pd.DataFrame(risultati)
    # Ritorna i primi 30 oggetti con lo Score più alto
    return df_final.sort_values(by="Buy Score", ascending=False).head(30)
