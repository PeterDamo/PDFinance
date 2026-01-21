import yfinance as yf
import pandas as pd
import requests

def get_market_tickers():
    tickers = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # Wikipedia: S&P 500
        sp500 = pd.read_html(requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", headers=headers).text)[0]
        tickers.extend(sp500['Symbol'].tolist())
        # Wikipedia: NASDAQ-100
        nasdaq = pd.read_html(requests.get("https://en.wikipedia.org/wiki/Nasdaq-100", headers=headers).text)[4]
        tickers.extend(nasdaq['Ticker'].tolist())
    except: pass
    
    # ETF Leader
    tickers.extend(["SPY", "QQQ", "DIA", "IWM", "VGT", "SCHD", "GLD", "IBIT"])
    return list(set(tickers))

def analizza_mercato_completo():
    all_tickers = get_market_tickers()
    risultati = []
    
    for ticker in all_tickers[:550]: # Limite per stabilità
        try:
            symbol = str(ticker).replace('.', '-')
            t = yf.Ticker(symbol)
            hist = t.history(period="3y")
            if hist.empty: continue
            
            info = t.info
            curr_p = info.get('currentPrice') or hist['Close'].iloc[-1]
            
            # Dividendo corretto in percentuale
            div_raw = info.get('dividendYield') or info.get('trailingAnnualDividendYield') or 0
            div_perc = float(div_raw) * 100 
            
            # Performance anni solari
            h24 = hist[hist.index.year == 2024]
            p24 = ((h24['Close'].iloc[-1] / h24['Close'].iloc[0]) - 1) * 100 if not h24.empty else 0
            h25 = hist[hist.index.year == 2025]
            p25 = ((h25['Close'].iloc[-1] / h25['Close'].iloc[0]) - 1) * 100 if not h25.empty else 0
            
            # Previsione 2026 (Analisti o Trend)
            target = info.get('targetMeanPrice')
            prev_2026 = ((target / curr_p) - 1) * 100 if target else p25 * 0.7
            
            # Score Sentiment
            score = 0
            sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            if curr_p > sma50: score += 30
            if prev_2026 > 10: score += 40
            if 'buy' in str(info.get('recommendationKey', '')).lower(): score += 30

            risultati.append({
                "Codice": symbol,
                "Nome": info.get('longName', symbol),
                "Tipo": "ETF" if info.get('quoteType') == 'ETF' else "Azione",
                "Settore": info.get('sector') or info.get('category', 'N/A'),
                "Dividendo (%)": round(div_perc, 2),
                "Perf. 2024 (%)": round(p24, 2),
                "Perf. 2025 (%)": round(p25, 2),
                "Previsione 2026 (%)": round(prev_2026, 2),
                "Buy Score": score,
                "TradingView": f"https://www.tradingview.com/symbols/{symbol}/"
            })
        except: continue
            
    return pd.DataFrame(risultati).sort_values(by="Buy Score", ascending=False).head(30)
