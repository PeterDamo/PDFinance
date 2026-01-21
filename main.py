import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# 1. Configurazione Interfaccia
st.set_page_config(page_title="Dynamic Global Screener 2026", layout="wide")

# Stile: Sfondo Bianco, Testi Grigio Scuro (#333333), Pulsanti Grigio Chiaro
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
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .news-title { font-weight: bold; color: #222222 !important; }
    .news-meta { color: #777777 !important; font-size: 0.85em; }
    </style>
    """, unsafe_allow_html=True)

# --- MOTORE DI RECUPERO TITOLI (100% DINAMICO) ---

@st.cache_data(ttl=3600)
def get_global_pool():
    """Recupera dinamicamente i ticker da S&P 500 e Mercato Italiano"""
    tickers = []
    # 1. S&P 500 da Wikipedia
    try:
        sp_url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        sp_table = pd.read_html(sp_url)[0]
        tickers.extend(sp_table['Symbol'].tolist())
    except: pass

    # 2. Italia Most Active da Yahoo
    try:
        it_url = "https://finance.yahoo.com/markets/stocks/most-active/?lookup=MI&auto_prefill=MI"
        res = requests.get(it_url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        for a in soup.find_all('a'):
            href = a.get('href', '')
            if '/quote/' in href:
                sym = href.split('/quote/')[1].split('?')[0].split('/')[0]
                if ".MI" in sym: tickers.append(sym)
    except: pass
    
    return list(set(tickers))

# --- ANALISI MULTIFATTORIALE ---

def analizza_sentiment_e_trend(symbol):
    """Calcola Crescite Storiche, Sentiment e Trend di Settore"""
    try:
        t = yf.Ticker(symbol)
        hist = t.history(period="3y") # Dati dal 2024 al 2026
        if hist.empty or len(hist) < 100: return None
        
        info = t.info
        curr_p = info.get('currentPrice') or hist['Close'].iloc[-1]
        target = info.get('targetMeanPrice')
        
        # 1. Calcolo Crescite (Anti-KeyError)
        h24 = hist[hist.index.year == 2024]
        c24 = ((h24['Close'].iloc[-1] / h24['Close'].iloc[0]) - 1) * 100 if not h24.empty else 0
        
        h25 = hist[hist.index.year == 2025]
        c25 = ((h25['Close'].iloc[-1] / h25['Close'].iloc[0]) - 1) * 100 if not h25.empty else 0
        
        upside_26 = ((target / curr_p) - 1) * 100 if target else 0
        
        # 2. Sentiment Score (0-100)
        score = 0
        sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        if curr_p > sma50: score += 35 # Trend Tecnico
        if upside_26 > 12: score += 40 # Previsione Analisti
        if info.get('recommendationKey') in ['buy', 'strong_buy']: score += 25 # Consenso
        
        label = "Strong Buy 🔥" if score >= 80 else "Bullish 📈" if score >= 50 else "Neutral ⚖️"
        
        return {
            "Azienda": info.get('longName', symbol[:15]),
            "Ticker": symbol,
            "Settore": info.get('sector', 'N/A'),
            "Sentiment": label,
            "Crescita 2024 (%)": round(c24, 2),
            "Crescita 2025 (%)": round(c25, 2),
            "Prevista 2026 (%)": round(upside_26, 2),
            "Score": score
        }
    except: return None

# --- UI E ESECUZIONE ---

st.title("🏹 Market Hunter 2026: S&P 500 & Italia")
st.write("Analisi dinamica basata su **Sentiment**, **Crescita Storica** e **Target Price 2026**.")

if st.button('🚀 AVVIA ANALISI DINAMICA DEI 30 MIGLIORI TITOLI'):
    with st.spinner('Scansione mercati globali in corso...'):
        pool = get_global_pool()
        # Campionamento per prestazioni (analizziamo i più rilevanti)
        sample_pool = pool[:60] if len(pool) > 60 else pool
        
        risultati = []
        news_list = []
        bar = st.progress(0)
        
        for i, s in enumerate(sample_pool):
            data = analizza_titolo_robusto = analizza_sentiment_e_trend(s)
            if data: risultati.append(data)
            bar.progress((i + 1) / len(sample_pool))
        
        if risultati:
            df = pd.DataFrame(risultati).sort_values(by="Score", ascending=False).head(30)
            st.session_state.df_final = df
            
            # Recupero news per i top
            for s in df['Ticker'].head(12):
                try:
                    raw = yf.Ticker(s).news[0]
                    news_list.append({
                        "t": s, "n": df[df['Ticker']==s]['Azienda'].values[0],
                        "title": raw['title'], "pub": raw['publisher']
                    })
                except: continue
            st.session_state.news_final = news_list

if 'df_final' in st.session_state:
    st.subheader("📊 Classifica Dinamica: I migliori 30 titoli del momento")
    st.dataframe(
        st.session_state.df_final.drop(columns=['Score']),
        column_config={
            "Crescita 2024 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Crescita 2025 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Prevista 2026 (%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
        hide_index=True, use_container_width=True
    )
    
    st.divider()
    
    st.subheader("📰 Sentiment News: I Leader del Settore")
    c1, c2 = st.columns(2)
    for idx, n in enumerate(st.session_state.news_final):
        with (c1 if idx % 2 == 0 else c2):
            st.markdown(f"""
                <div class="news-card">
                    <span class="news-title">{n['n']} ({n['t']})</span><br>
                    <p style='color:#444; margin:8px 0;'>{n['title']}</p>
                    <span class="news-meta"><b>{n['pub']}</b> • 2026 Feed</span>
                </div>
            """, unsafe_allow_html=True)

    # Download
    csv = st.session_state.df_final.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Esporta Report Strategico", csv, "Top30_Sentiment_2026.csv", "text/csv")
