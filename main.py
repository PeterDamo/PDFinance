import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# Configurazione Pagina e Stile Moderno
st.set_page_config(page_title="Analisi Settoriale 2026", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .stButton>button {
        background-color: #e9ecef !important;
        color: #495057 !important;
        border: 1px solid #ced4da !important;
        border-radius: 10px !important;
    }
    .news-card {
        background-color: #f8f9fa; padding: 15px; border-radius: 10px;
        border-left: 6px solid #007bff; margin-bottom: 12px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏹 Market Insight 2026: Titoli vs Settore")
st.write("Confronto dinamico tra la crescita del titolo e il trend del suo settore di appartenenza.")

# Mappatura dei settori principali con i loro ETF di riferimento (Benchmark)
SECTOR_BENCHMARKS = {
    'Technology': 'XLK',
    'Financial Services': 'XLF',
    'Healthcare': 'XLV',
    'Consumer Cyclical': 'XLY',
    'Communication Services': 'XLC',
    'Industrials': 'XLI',
    'Energy': 'XLE',
    'Utilities': 'XLU',
    'Real Estate': 'XLRE',
    'Consumer Defensive': 'XLP'
}

def get_sector_growth(sector_name):
    """Calcola la crescita media del settore nell'anno in corso"""
    ticker_symbol = SECTOR_BENCHMARKS.get(sector_name, 'SPY') # Default su S&P 500
    try:
        etf = yf.Ticker(ticker_symbol)
        hist = etf.history(period="1y")
        growth = ((hist['Close'].iloc[-1] - hist['Close'].iloc[0]) / hist['Close'].iloc[0]) * 100
        return round(growth, 2)
    except:
        return 0.0

def esegui_scansione_settoriale():
    # Recupero dinamico dei titoli più attivi
    headers = {'User-Agent': 'Mozilla/5.0'}
    pool = []
    urls = ["https://finance.yahoo.com/most-active", "https://finance.yahoo.com/markets/stocks/most-active/?lookup=MI&auto_prefill=MI"]
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if '/quote/' in href:
                    s = href.split('/quote/')[1].split('?')[0].split('/')[0]
                    if s not in pool: pool.append(s)
        except: continue

    risultati = []
    news_feed = []
    progresso = st.progress(0)
    
    for i, symbol in enumerate(pool[:30]): # Analizziamo i primi 30 per velocità
        try:
            t = yf.Ticker(symbol)
            info = t.info
            hist = t.history(start="2024-01-01")
            
            if not hist.empty:
                # 1. Crescita Storica Titolo
                c_24 = ((hist.loc['2024-12-31']['Close'].iloc[0] / hist.loc['2024-01-01']['Close'].iloc[0]) - 1) * 100
                c_25 = ((hist.loc['2025-12-31']['Close'].iloc[0] / hist.loc['2025-01-01']['Close'].iloc[0]) - 1) * 100
                
                # 2. Crescita Prevista 2026
                p_attuale = info.get('currentPrice', hist['Close'].iloc[-1])
                target = info.get('targetMeanPrice')
                c_prev_26 = ((target / p_attuale) - 1) * 100 if target else 0
                
                # 3. Trend di Settore
                settore = info.get('sector', 'N/A')
                trend_settore = get_sector_growth(settore)
                
                risultati.append({
                    "Azienda": info.get('longName', symbol),
                    "Settore": settore,
                    "Crescita 2024 (%)": round(c_24, 2),
                    "Crescita 2025 (%)": round(c_25, 2),
                    "Prevista 2026 (%)": round(c_prev_26, 2),
                    "Trend Settore (%)": trend_settore,
                    "Performance vs Settore": "Sopra Media 🚀" if c_prev_26 > trend_settore else "In Linea ⚖️"
                })
        except: continue
        progresso.progress((i + 1) / 30)
    
    return pd.DataFrame(risultati)

# --- UI ---
if st.button('🚀 AVVIA ANALISI COMPARATIVA DI SETTORE'):
    df = esegui_scansione_settoriale()
    st.session_state.df_settore = df

if 'df_settore' in st.session_state:
    st.subheader("📊 Report Strategico: Titolo vs Mercato")
    st.dataframe(
        st.session_state.df_settore,
        column_config={
            "Crescita 2024 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Crescita 2025 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Prevista 2026 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Trend Settore (%)": st.column_config.NumberColumn(format="%.2f%%")
        },
        hide_index=True, use_container_width=True
    )
    
    # Download
    csv = st.session_state.df_settore.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Report Completo", csv, "analisi_settoriale.csv", "text/csv")
