import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# 1. Configurazione Pagina
st.set_page_config(page_title="S&P 500 Dynamic Hunter", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3, p, span, .stMarkdown { color: #333333 !important; }
    .stButton>button {
        background-color: #eeeeee !important;
        color: #444444 !important;
        border: 1px solid #cccccc !important;
        border-radius: 8px !important;
        font-weight: 600;
        width: 100%;
    }
    .news-card {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 12px;
        border-left: 6px solid #444444;
        margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- RECUPERO TITOLI 100% DINAMICO (Multi-Livello) ---

def get_sp500_dynamic():
    """Recupera la lista dei titoli in modo dinamico con fallback automatico"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # LIVELLO 1: Wikipedia (Standard S&P 500)
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        return tables[0]['Symbol'].tolist()
    except:
        pass

    # LIVELLO 2: Yahoo Finance Most Active (USA Market)
    try:
        url = "https://finance.yahoo.com/markets/stocks/most-active/"
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        tickers = []
        for a in soup.find_all('a'):
            href = a.get('href', '')
            if '/quote/' in href:
                sym = href.split('/quote/')[1].split('?')[0].split('/')[0]
                if sym.isalpha() and len(sym) < 6: tickers.append(sym)
        if tickers: return list(set(tickers))
    except:
        pass

    # LIVELLO 3: SlickCharts (S&P 500 Weights)
    try:
        url = "https://www.slickcharts.com/sp500"
        res = requests.get(url, headers=headers, timeout=5)
        df = pd.read_html(res.text)[0]
        return df['Symbol'].tolist()
    except:
        # Estremo rimedio: se internet è parzialmente bloccato, restituiamo i top 10 storici
        return ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA', 'AVGO', 'BRK.B', 'LLY']

# --- MOTORE DI ANALISI E RANKING ---

def esegui_scansione_sentiment():
    all_tickers = get_sp500_dynamic()
    results = []
    news_feed = []
    
    # Campionamento dinamico per velocità (i primi 70 per estrarre i 30 migliori)
    pool = all_tickers[:70]
    
    status = st.empty()
    bar = st.progress(0)
    
    for i, sym in enumerate(pool):
        status.markdown(f"<span style='color:#444'>Analisi Sentiment Dinamica: **{sym}**...</span>", unsafe_allow_html=True)
        try:
            # Sostituiamo il punto con il trattino per ticker come BRK.B
            clean_sym = sym.replace('.', '-')
            t = yf.Ticker(clean_sym)
            hist = t.history(period="2y")
            if hist.empty: continue
            
            info = t.info
            curr_p = info.get('currentPrice') or hist['Close'].iloc[-1]
            target = info.get('targetMeanPrice')
            
            # Calcolo Crescita Annuale (Metodo robusto)
            h24 = hist[hist.index.year == 2024]
            c24 = ((h24['Close'].iloc[-1] / h24['Close'].iloc[0]) - 1) * 100 if not h24.empty else 0
            
            h25 = hist[hist.index.year == 2025]
            c25 = ((h25['Close'].iloc[-1] / h25['Close'].iloc[0]) - 1) * 100 if not h25.empty else 0
            
            upside_26 = ((target / curr_p) - 1) * 100 if target else 0
            
            # ALGORITMO RANKING (Sentiment & Momentum)
            score = 0
            sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            if curr_p > sma50: score += 40  # Trend Tecnico
            if upside_26 > 10: score += 40   # Analisti 2026
            if info.get('recommendationKey') in ['buy', 'strong_buy']: score += 20
            
            results.append({
                "Azienda": info.get('longName', sym),
                "Ticker": sym,
                "Sentiment": "🔥 Eccellente" if score >= 80 else "📈 Bullish" if score >= 50 else "⚖️ Neutro",
                "Crescita 2024 (%)": round(c24, 2),
                "Crescita 2025 (%)": round(c25, 2),
                "Prevista 2026 (%)": round(upside_26, 2),
                "Score": score,
                "TradingView": f"https://www.tradingview.com/symbols/{clean_sym}/"
            })
            
            if t.news:
                news_feed.append({"s": sym, "t": t.news[0]['title'], "p": t.news[0]['publisher']})
        except:
            continue
        bar.progress((i + 1) / len(pool))
        
    status.empty()
    # RITORNA I 30 MIGLIORI DINAMICI
    df_final = pd.DataFrame(results).sort_values(by="Score", ascending=False).head(30)
    return df_final, news_feed

# --- INTERFACCIA ---

st.title("🏹 Market Hunter 2026: S&P 500 Dynamic Elite")
st.write("I 30 titoli con il sentiment più forte estratti in tempo reale dai mercati USA.")

if st.button('🚀 AVVIA ANALISI DINAMICA'):
    df_res, news_res = esegui_scansione_sentiment()
    st.session_state.df_hunter = df_res
    st.session_state.news_hunter = news_res

if 'df_hunter' in st.session_state:
    st.subheader("📊 Top 30 Titoli per Sentiment e Potenziale")
    st.dataframe(
        st.session_state.df_hunter.drop(columns=['Score']),
        column_config={
            "TradingView": st.column_config.LinkColumn("Grafico", display_text="Apri TV 📈"),
            "Crescita 2024 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Crescita 2025 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Prevista 2026 (%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
        hide_index=True, use_container_width=True
    )
    
    st.divider()
    
    st.subheader("📰 Sentiment News Feed")
    c1, c2 = st.columns(2)
    for idx, n in enumerate(st.session_state.news_hunter[:12]):
        with (c1 if idx % 2 == 0 else c2):
            st.markdown(f"""
                <div class="news-card">
                    <b>{n['s']}</b>: {n['t']}<br>
                    <small style='color:#666;'>Fonte: {n['p']}</small>
                </div>
            """, unsafe_allow_html=True)
