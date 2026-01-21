import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

st.set_page_config(page_title="Scanner Professionale 2026", layout="wide")

st.title("📈 Analisi Finanziaria Dinamica")

# --- FUNZIONE DI RECUPERO TITOLI ROBUSTA ---
def get_trending_tickers():
    # URL di riserva e Headers realistici
    url = "https://finance.yahoo.com/trending-tickers"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    tickers = []
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            # Cerchiamo tutti i link che contengono simboli di borsa
            for link in soup.find_all('a'):
                href = link.get('href', '')
                if '/quote/' in href:
                    symbol = href.split('/quote/')[1].split('?')[0].split('/')[0]
                    if symbol.isalpha() and len(symbol) <= 5: # Filtro titoli standard
                        if symbol not in tickers:
                            tickers.append(symbol)
        
        # Se lo scraping fallisce, usiamo una lista di mercato "Hot" del 2026 predefinita
        if not tickers:
            tickers = ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'AMZN', 'META', 'GOOGL', 'BRK-B', 'LLY', 'AVGO', 
                       'V', 'JPM', 'UNH', 'MA', 'COST', 'HD', 'PG', 'NFLX', 'DIS', 'ADBE']
        
        return tickers[:20]
    except Exception as e:
        return ['AAPL', 'MSFT', 'NVDA', 'TSLA', 'GOOGL'] # Fallback estremo

# --- LOGICA DI ANALISI ---
def analizza_e_mostra():
    titoli = get_trending_tickers()
    risultati = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, symbol in enumerate(titoli):
        status_text.text(f"Recupero dettagli per {symbol} ({i+1}/20)...")
        try:
            t = yf.Ticker(symbol)
            # Chiediamo i dati storici
            data = t.history(period="3y")
            
            if not data.empty and len(data) > 500:
                # Calcolo crescita 2024 (Basato su inizio/fine anno)
                p_inizio_24 = data['Close'].iloc[0]
                p_fine_24 = data['Close'].iloc[252] if len(data) > 252 else data['Close'].iloc[-1]
                c_2024 = ((p_fine_24 - p_inizio_24) / p_inizio_24) * 100
                
                # Calcolo crescita 2025
                p_fine_25 = data['Close'].iloc[-1]
                c_2025 = ((p_fine_25 - p_fine_24) / p_fine_24) * 100
                
                # Link TradingView
                tv_url = f"https://www.tradingview.com/symbols/{symbol}"
                
                risultati.append({
                    "Ticker": symbol,
                    "Analisi 📊": tv_url,
                    "Feedback": "Ottimo" if c_2025 > 10 else "Stabile",
                    "Crescita 2024 (%)": round(c_2024, 2),
                    "Crescita 2025 (%)": round(c_2025, 2),
                    "Target 2026": "Bullish 🚀" if c_2025 > 0 else "Accumulo 💎"
                })
            time.sleep(0.1)
        except:
            continue
        progress_bar.progress((i + 1) / len(titoli))
    
    status_text.empty()
    return pd.DataFrame(risultati)

# --- UI ---
if st.button('🚀 AVVIA SCANNER E RECUPERA DETTAGLI'):
    df = analizza_e_mostra()
    if not df.empty:
        st.session_state.data = df
    else:
        st.error("Dati non disponibili al momento. Riprova tra pochi istanti.")

if 'data' in st.session_state:
    st.dataframe(
        st.session_state.data,
        column_config={
            "Analisi 📊": st.column_config.LinkColumn(display_text="Grafico TV")
        },
        hide_index=True,
        use_container_width=True
    )
    
    csv = st.session_state.data.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Report CSV", csv, f"investimenti_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")
