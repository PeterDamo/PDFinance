import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import time

# 1. Configurazione Pagina
st.set_page_config(page_title="Scanner Finanziario 2026", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .stButton>button { background-color: #e9ecef !important; color: #495057 !important; border-radius: 10px !important; width: 100%; }
    .news-card { background-color: #f8f9fa; padding: 15px; border-radius: 10px; border-left: 6px solid #007bff; margin-bottom: 12px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🏹 Analizzatore Strategico 2026")
st.write("Se l'analisi non parte, assicurati di avere una connessione internet attiva.")

# --- FUNZIONI DI SUPPORTO ---
def safe_get_growth(hist_data):
    """Calcola la crescita in modo sicuro gestendo i dati mancanti"""
    try:
        if len(hist_data) < 2: return 0.0
        inizio = hist_data.iloc[0]
        fine = hist_data.iloc[-1]
        return round(((fine - inizio) / inizio) * 100, 2)
    except:
        return 0.0

def get_dynamic_tickers():
    """Recupera ticker attivi da Yahoo Finance"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    tickers = []
    # Proviamo a prendere i più attivi
    try:
        url = "https://finance.yahoo.com/most-active"
        res = requests.get(url, headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        for a in soup.find_all('a'):
            href = a.get('href', '')
            if '/quote/' in href:
                sym = href.split('/quote/')[1].split('?')[0].split('/')[0]
                if sym.isalpha() and len(sym) < 6 and sym not in tickers:
                    tickers.append(sym)
    except:
        pass
    
    # Se lo scraping fallisce, carichiamo una lista d'emergenza (Global + IT)
    if not tickers:
        tickers = ['NVDA', 'AAPL', 'TSLA', 'MSFT', 'ENEL.MI', 'ISP.MI', 'UCG.MI', 'ASML', 'NVO', 'AMZN']
    
    return tickers[:25]

# --- CORE LOGIC ---
def esegui_analisi():
    pool = get_dynamic_tickers()
    risultati = []
    news_feed = []
    
    progresso = st.progress(0)
    status = st.empty()

    for i, symbol in enumerate(pool):
        status.info(f"Analisi in corso: **{symbol}**...")
        try:
            t = yf.Ticker(symbol)
            # Scarichiamo dati dal 2024 al 2026
            hist = t.history(start="2024-01-01")
            
            if not hist.empty:
                # Suddivisione anni
                df_2024 = hist.loc['2024-01-01':'2024-12-31']['Close']
                df_2025 = hist.loc['2025-01-01':'2025-12-31']['Close']
                df_2026 = hist.loc['2026-01-01':]['Close']
                
                # Calcolo Crescite
                c24 = safe_get_growth(df_2024)
                c25 = safe_get_growth(df_2025)
                
                # Crescita prevista (Target Analisti)
                info = t.info
                p_current = info.get('currentPrice', hist['Close'].iloc[-1])
                p_target = info.get('targetMeanPrice')
                c_prev_26 = round(((p_target - p_current) / p_current) * 100, 2) if p_target else 0.0
                
                # Trend Settore (Simulato per velocità o preso da ETF)
                settore = info.get('sector', 'N/A')
                
                risultati.append({
                    "Azienda": info.get('longName', symbol),
                    "Ticker": symbol,
                    "Settore": settore,
                    "Crescita 2024 (%)": c24,
                    "Crescita 2025 (%)": c25,
                    "Prevista 2026 (%)": c_prev_26,
                    "Analisi": f"https://www.tradingview.com/symbols/{symbol}"
                })
                
                if t.news:
                    n = t.news[0]
                    news_feed.append({
                        "name": info.get('longName', symbol),
                        "title": n['title'],
                        "date": datetime.fromtimestamp(n['providerPublishTime']).strftime('%d/%m/%Y')
                    })
            time.sleep(0.1)
        except Exception as e:
            continue
        progresso.progress((i + 1) / len(pool))
    
    status.empty()
    return pd.DataFrame(risultati), news_feed

# --- INTERFACCIA ---
if st.button('🚀 AVVIA ANALISI DINAMICA'):
    df, news = esegui_analisi()
    if not df.empty:
        st.session_state.data = df
        st.session_state.news = news
    else:
        st.error("Errore: Il server non ha restituito dati. Riprova tra un minuto.")

if 'data' in st.session_state:
    st.subheader("📊 Risultati Analisi Storica e Previsionale")
    st.dataframe(
        st.session_state.data,
        column_config={"Analisi": st.column_config.LinkColumn(display_text="Grafico 📈")},
        hide_index=True, use_container_width=True
    )
    
    # Download
    csv = st.session_state.data.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Report CSV", csv, "report_2026.csv", "text/csv")

    st.divider()
    st.subheader("📰 Ultime Notizie")
    cols = st.columns(2)
    for idx, n in enumerate(st.session_state.news[:12]):
        with cols[idx % 2]:
            st.markdown(f'<div class="news-card"><b>{n["name"]}</b><br>{n["title"]}<br><small>{n["date"]}</small></div>', unsafe_allow_html=True)
