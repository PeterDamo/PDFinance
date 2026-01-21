import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# Configurazione Pagina e Stile
st.set_page_config(page_title="Scanner Dinamico Totale 2026", layout="wide")

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

st.title("🏹 Global & Italy Scanner 2026")
st.write("Analisi automatica basata sui titoli più attivi del giorno nei mercati USA ed EU (Italia inclusa).")

# --- 1. FUNZIONE PER GENERARE WATCHLIST ITALIANA E GLOBALE DINAMICAMENTE ---
def get_all_dynamic_tickers():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    all_tickers = []
    
    # URL 1: Titoli Globali più attivi
    url_global = "https://finance.yahoo.com/most-active"
    # URL 2: Titoli Italiani (Borsa Italiana) - Cerchiamo i simboli con .MI
    url_italy = "https://finance.yahoo.com/markets/stocks/most-active/?lookup=MI&auto_prefill=MI"

    sources = [url_global, url_italy]
    
    for url in sources:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if '/quote/' in href:
                    symbol = href.split('/quote/')[1].split('?')[0].split('/')[0]
                    if symbol not in all_tickers:
                        all_tickers.append(symbol)
        except:
            continue
            
    return all_tickers[:50] # Prendiamo un pool di 50 titoli da filtrare

# --- 2. LOGICA DI ANALISI E FILTRO SMART ---
def esegui_scansione_totale():
    pool = get_all_dynamic_tickers()
    risultati = []
    news_feed = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, symbol in enumerate(pool):
        status_text.text(f"Analisi dinamica in corso: {symbol}...")
        try:
            t = yf.Ticker(symbol)
            # Analizziamo gli ultimi 2 anni per avere i dati 2024-2025 e l'inizio del 2026
            hist = t.history(period="2y")
            
            if not hist.empty and len(hist) > 100:
                # Calcoli Crescita
                p_inizio_26 = hist['Close'].iloc[0] # Riferimento dinamico
                p_attuale = hist['Close'].iloc[-1]
                crescita_26 = ((p_attuale - p_inizio_26) / p_inizio_26) * 100
                
                # Criterio di "Sottovalutazione" e Trend
                # Un titolo è considerato interessante se il prezzo attuale è sopra la media mobile a 50gg
                sma_50 = hist['Close'].rolling(window=50).mean().iloc[-1]
                
                # Mostriamo solo titoli con trend positivo
                if crescita_26 > 0 and p_attuale > sma_50:
                    info = t.info
                    risultati.append({
                        "Mercato": "Italia 🇮🇹" if ".MI" in symbol else "Globale 🌐",
                        "Azienda": info.get('longName', symbol),
                        "Ticker": symbol,
                        "Crescita (%)": round(crescita_26, 2),
                        "Analisi": f"https://www.tradingview.com/symbols/{symbol.replace('.MI', '')}",
                        "Sentiment": "Bullish 🚀"
                    })
                    
                    if t.news:
                        n = t.news[0]
                        news_feed.append({
                            "name": info.get('longName', symbol),
                            "title": n['title'],
                            "date": datetime.fromtimestamp(n['providerPublishTime']).strftime('%d/%m/%Y'),
                            "publisher": n['publisher']
                        })
            time.sleep(0.1) # Evita il blocco dal server
        except:
            continue
        progress_bar.progress((i + 1) / len(pool))
    
    status_text.empty()
    # Ordiniamo per crescita e prendiamo i primi 20
    df = pd.DataFrame(risultati).sort_values(by="Crescita (%)", ascending=False).head(20)
    return df, news_feed

# --- INTERFACCIA ---
if st.button('🔄 AVVIA SCANSIONE MERCATO ITALIA E MONDO'):
    df, news = esegui_scansione_totale()
    st.session_state.master_df = df
    st.session_state.master_news = news

if 'master_df' in st.session_state:
    st.subheader("📊 Top 20 Opportunità Sottovalutate in Espansione")
    st.dataframe(
        st.session_state.master_df,
        column_config={"Analisi": st.column_config.LinkColumn("Grafico", display_text="Dettagli 📈")},
        hide_index=True, use_container_width=True
    )
    
    st.divider()
    st.subheader("📰 Notizie ed Eventi Rilevanti")
    c1, c2 = st.columns(2)
    for idx, n in enumerate(st.session_state.master_news[:14]):
        with (c1 if idx % 2 == 0 else c2):
            st.markdown(f"""
                <div class="news-card">
                    <b>{n['name']}</b><br>{n['title']}<br>
                    <small>{n['publisher']} | {n['date']}</small>
                </div>
            """, unsafe_allow_html=True)
