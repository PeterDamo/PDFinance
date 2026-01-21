import yfinance as yf
import pandas as pd
import requests
import streamlit as st

@st.cache_data(ttl=3600)
def get_market_tickers():
    tickers = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        df_sp = pd.read_html(requests.get("https://en.wikipedia.org/wiki/List_of_S%26P_500_companies", headers=headers).text)[0]
        tickers.extend(df_sp['Symbol'].tolist())
        df_nd = pd.read_html(requests.get("https://en.wikipedia.org/wiki/Nasdaq-100", headers=headers).text)[4]
        tickers.extend(df_nd['Ticker'].tolist())
    except: pass
    tickers.extend(["SPY", "QQQ", "DIA", "IWM", "VGT", "SCHD", "VIG", "GLD", "IBIT"])
    return list(set(tickers))

def processa_dati_base():
    """Funzione interna per processare i dati grezzi comuni ad entrambe le tabelle."""
    all_tickers = get_market_tickers()
    risultati = []
    for ticker in all_tickers[:550]:
        try:
            symbol = str(ticker).replace('.', '-')
            t = yf.Ticker(symbol)
            hist = t.history(period="3y")
            if hist.empty: continue
            
            info = t.info
            curr_p = info.get('currentPrice') or hist['Close'].iloc[-1]
            div_raw = info.get('dividendYield') or info.get('trailingAnnualDividendYield') or 0
            div_val = float(div_raw or 0) / 100 
            
            h24 = hist[hist.index.year == 2024]; p24 = ((h24['Close'].iloc[-1] / h24['Close'].iloc[0]) - 1) * 100 if not h24.empty else 0
            h25 = hist[hist.index.year == 2025]; p25 = ((h25['Close'].iloc[-1] / h25['Close'].iloc[0]) - 1) * 100 if not h25.empty else 0
            
            target = info.get('targetMeanPrice')
            prev_2026 = ((target / curr_p) - 1) * 100 if target else p25 * 0.7
            
            # Sentiment Score
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
                "Dividendo (%)": div_val,
                "Perf. 2024 (%)": p24,
                "Perf. 2025 (%)": p25,
                "Previsione 2026 (%)": prev_2026,
                "Buy Score": score,
                "TradingView": f"https://www.tradingview.com/symbols/{symbol}/"
            })
        except: continue
    return pd.DataFrame(risultati)

@st.cache_data(ttl=3600)
def analizza_mercato_completo():
    df = processa_dati_base()
    return df.sort_values(by="Buy Score", ascending=False).head(30)

@st.cache_data(ttl=3600)
def analizza_top_dividendi():
    df = processa_dati_base()
    # Algoritmo: Dividendo pesato + Performance 2025 + Sentiment
    # Filtriamo titoli con dividendo > 1.5% e score sentiment decente
    df_div = df[df['Dividendo (%)'] > 0.015].copy()
    df_div['Rank_Div'] = (df_div['Dividendo (%)'] * 100) + (df_div['Perf. 2025 (%)'] * 0.5) + (df_div['Buy Score'] * 0.3)
    return df_div.sort_values(by="Rank_Div", ascending=False).head(15)
