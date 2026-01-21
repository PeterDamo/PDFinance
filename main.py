import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# 1. Configurazione Pagina
st.set_page_config(page_title="Top 30 Global & Italy 2026", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3, span, p, .stMarkdown { color: #333333 !important; }
    .stButton>button {
        background-color: #eeeeee !important;
        color: #444444 !important;
        border: 1px solid #cccccc !important;
        border-radius: 8px !important;
        font-weight: 600;
        width: 100%;
    }
    .news-card {
        background-color: #fcfcfc;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #333333;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- MOTORE DI RECUPERO DINAMICO ---

@st.cache_data(ttl=3600)
def get_sp500_tickers():
    """Recupera la lista aggiornata dell'S&P 500 da Wikipedia"""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        res = requests.get(url)
        df = pd.read_html(res.text)[0]
        return df['Symbol'].tolist()
    except:
        return ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'TSLA']

def get_italy_tickers():
    """Recupera i titoli più attivi di Borsa Italiana"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    tickers = []
    url = "https://finance.yahoo.com/markets/stocks/most-active/?lookup=MI&auto_prefill=MI"
    try:
        res = requests.get(url, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        for a in soup.find_all('a'):
            href = a.get('href', '')
            if '/quote/' in href:
                sym = href.split('/quote/')[1].split('?')[0].split('/')[0]
                if ".MI" in sym: tickers.append(sym)
    except: pass
    return tickers

# --- LOGICA DI ANALISI ---

def analizza_titolo_robusto(symbol):
    """Analisi tecnica e previsionale con protezione anti-crash"""
    try:
        t = yf.Ticker(symbol)
        # Scarichiamo dati sufficienti per 2024, 2025 e 2026
        hist = t.history(period="3y") 
        if hist.empty or len(hist) < 100: return None
        
        info = t.info
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or hist['Close'].iloc[-1]
        
        # --- CALCOLO STORICO (Anti-KeyError: usiamo il filtraggio per anno) ---
        # 2024
        h24 = hist[hist.index.year == 2024]
        c24 = ((h24['Close'].iloc[-1] / h24['Close'].iloc[0]) - 1) * 100 if not h24.empty else 0
        
        # 2025
        h25 = hist[hist.index.year == 2025]
        c25 = ((h25['Close'].iloc[-1] / h25['Close'].iloc[0]) - 1) * 100 if not h25.empty else 0

        # --- PREVISIONI 2026 ---
        target = info.get('targetMeanPrice')
        upside = ((target / current_price) - 1) * 100 if target else 0
        
        # Sentiment Score
        score = 0
        sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        if current_price > sma50: score += 40
        if upside > 15: score += 40
        if info.get('recommendationKey') in ['buy', 'strong_buy']: score += 20
        
        if score < 30: return None # Filtro qualità

        return {
            "Mercato": "Italia 🇮🇹" if ".MI" in symbol else "USA 🇺🇸",
            "Azienda": info.get('longName', symbol[:15]),
            "Ticker": symbol,
            "Crescita 2024 (%)": round(c24, 2),
            "Crescita 2025 (%)": round(c25, 2),
            "Upside 2026 (%)": round(upside, 2),
            "Sentiment": "Ottimo 🔥" if score >= 80 else "Buono 📈" if score >= 50 else "Stabile ⚖️",
            "Score": score
        }
    except: return None

# --- UI ---

st.title("🎯 Top 30 Market Scanner: S&P 500 & Italia")
st.write("Analisi dinamica basata su dati real-time. Sentiment e Previsioni 2026.")

if st.button('🚀 AVVIA SCANSIONE COMPLETA'):
    with st.spinner('Recupero liste mercati e analisi in corso...'):
        # 1. Creazione Pool Dinamico
        sp500 = get_sp500_tickers()[:40] # Campionamento per velocità
        italy = get_italy_tickers()
        pool = list(set(sp500 + italy))
        
        risultati = []
        news_list = []
        progresso = st.progress(0)
        
        # 2. Loop di analisi
        for i, s in enumerate(pool):
            data = analizza_titolo_robusto(s)
            if data: risultati.append(data)
            progresso.progress((i + 1) / len(pool))
        
        # 3. Ordinamento e selezione Top 30
        if risultati:
            df = pd.DataFrame(risultati).sort_values(by="Score", ascending=False).head(30)
            st.session_state.top30 = df
            
            # Recupero news per i top 10
            for s in df['Ticker'].head(10):
                try:
                    n = yf.Ticker(s).news[0]
                    news_list.append({
                        "t": s, "title": n['title'], "pub": n['publisher']
                    })
                except: continue
            st.session_state.top_news = news_list

if 'top30' in st.session_state:
    st.subheader("📊 Classifica Top 30 Titoli (Sentiment & Upside)")
    st.dataframe(
        st.session_state.top30.drop(columns=['Score']),
        column_config={
            "Crescita 2024 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Crescita 2025 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Upside 2026 (%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
        hide_index=True, use_container_width=True
    )
    
    st.divider()
    
    st.subheader("📰 Flash News Titoli Leader")
    c1, c2 = st.columns(2)
    for idx, n in enumerate(st.session_state.top_news):
        with (c1 if idx % 2 == 0 else c2):
            st.markdown(f"""<div class="news-card"><b>{n['t']}</b>: {n['title']}<br><small>{n['pub']}</small></div>""", unsafe_allow_html=True)

    csv = st.session_state.top30.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Report CSV", csv, "Top30_Global_IT.csv", "text/csv")
