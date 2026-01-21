import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# 1. Configurazione Pagina e Stile Professionale
st.set_page_config(page_title="S&P 500 Sentiment Elite", layout="wide")

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

# --- RECUPERO DINAMICO S&P 500 ---

@st.cache_data(ttl=86400) # Aggiorna la lista dell'indice una volta al giorno
def get_sp500_list():
    """Recupera l'elenco ufficiale dell'S&P 500 da Wikipedia"""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        tables = pd.read_html(url)
        df = tables[0]
        return df['Symbol'].tolist()
    except:
        return ['AAPL', 'MSFT', 'NVDA', 'AMZN', 'GOOGL', 'META', 'BRK.B', 'TSLA']

# --- MOTORE DI ANALISI SENTIMENT ---

def analizza_sentiment_sp500(ticker_list):
    """Analizza il sentiment dinamico per un pool di titoli"""
    results = []
    news_feed = []
    
    status = st.empty()
    bar = st.progress(0)
    
    # Per performance, analizziamo i primi 60 per trovare i 30 migliori (limitazione Streamlit)
    # Puoi aumentare il limite se hai una connessione veloce
    pool = ticker_list[:60] 
    
    for i, sym in enumerate(pool):
        status.markdown(f"<span style='color:#444'>Analisi Sentiment S&P 500: **{sym}**...</span>", unsafe_allow_html=True)
        try:
            t = yf.Ticker(sym)
            hist = t.history(period="3y")
            if hist.empty: continue
            
            info = t.info
            curr_price = info.get('currentPrice') or hist['Close'].iloc[-1]
            target = info.get('targetMeanPrice')
            
            # Calcolo Crescite (Robusto anti-KeyError)
            h24 = hist[hist.index.year == 2024]
            c24 = ((h24['Close'].iloc[-1] / h24['Close'].iloc[0]) - 1) * 100 if not h24.empty else 0
            
            h25 = hist[hist.index.year == 2025]
            c25 = ((h25['Close'].iloc[-1] / h25['Close'].iloc[0]) - 1) * 100 if not h25.empty else 0
            
            upside = ((target / curr_price) - 1) * 100 if target else 0
            
            # ALGORITMO SENTIMENT (Score 0-100)
            score = 0
            # Trend: Prezzo > Media 50 giorni
            sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            if curr_price > sma50: score += 40
            # Forecast: Upside > 15%
            if upside > 15: score += 40
            # Analyst Rating Buy
            if info.get('recommendationKey') in ['buy', 'strong_buy']: score += 20
            
            results.append({
                "Azienda": info.get('longName', sym),
                "Ticker": sym,
                "Sentiment": "💎 Eccellente" if score >= 80 else "📈 Positivo" if score >= 50 else "⚖️ Neutro",
                "Score": score,
                "Crescita 2024 (%)": round(c24, 2),
                "Crescita 2025 (%)": round(c25, 2),
                "Upside 2026 (%)": round(upside, 2),
                "TradingView": f"https://www.tradingview.com/symbols/{sym}/"
            })
            
            if t.news:
                news_feed.append({
                    "ticker": sym, "title": t.news[0]['title'], "pub": t.news[0]['publisher']
                })
        except: continue
        bar.progress((i + 1) / len(pool))
        
    status.empty()
    # Ordinamento Dinamico: i 30 titoli con lo Score più alto
    df_final = pd.DataFrame(results).sort_values(by="Score", ascending=False).head(30)
    return df_final, news_feed

# --- INTERFACCIA UTENTE ---

st.title("🏹 S&P 500: I 30 Leader del Sentiment 2026")
st.write("Analisi dinamica basata su **Consenso Analisti**, **Trend Tecnico** e **Potenziale 2026**.")

if st.button('🚀 GENERA TOP 30 S&P 500 IN TEMPO REALE'):
    tickers = get_sp500_list()
    df_top, news_top = analizza_sentiment_sp500(tickers)
    st.session_state.df_sp = df_top
    st.session_state.news_sp = news_top

if 'df_sp' in st.session_state:
    st.subheader("📊 Classifica dei 30 Titoli più Promettenti")
    st.dataframe(
        st.session_state.df_sp.drop(columns=['Score']),
        column_config={
            "TradingView": st.column_config.LinkColumn("Analisi Grafica", display_text="Vedi Grafico 📈"),
            "Crescita 2024 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Crescita 2025 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Upside 2026 (%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
        hide_index=True, use_container_width=True
    )
    
    st.divider()
    
    st.subheader("📰 Flash News: Top Pick del Momento")
    c1, c2 = st.columns(2)
    for idx, n in enumerate(st.session_state.news_sp[:12]):
        with (c1 if idx % 2 == 0 else c2):
            st.markdown(f"""
                <div class="news-card">
                    <b>{n['ticker']}</b>: {n['title']}<br>
                    <small style='color:#777;'>Fonte: {n['pub']}</small>
                </div>
            """, unsafe_allow_html=True)
    
    # Esportazione
    csv = st.session_state.df_sp.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Esporta Top 30 CSV", csv, "SP500_Top30_Sentiment.csv", "text/csv")
