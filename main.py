import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

st.set_page_config(page_title="Scanner Dettagliato 2026", layout="wide")

st.title("🔍 Scanner Finanziario Dinamico")
st.write("Analisi approfondita dei 20 titoli più caldi del momento.")

def get_trending_tickers():
    # Usiamo un URL affidabile per i titoli trending
    url = "https://finance.yahoo.com/trending-tickers"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        tickers = []
        # Cerchiamo i simboli all'interno delle celle della tabella (td)
        for td in soup.find_all('td', {'field': 'symbol'}):
            symbol = td.text.strip()
            if symbol not in tickers:
                tickers.append(symbol)
        return tickers[:20]
    except Exception as e:
        st.error(f"Errore nel recupero titoli: {e}")
        return ['AAPL', 'NVDA', 'TSLA', 'MSFT', 'AMZN']

def analizza_titoli(lista_ticker):
    risultati = []
    placeholder = st.empty() # Spazio per i messaggi di stato
    progresso = st.progress(0)
    
    for i, symbol in enumerate(lista_ticker):
        placeholder.write(f"Analizzando i dettagli di: **{symbol}**...")
        try:
            t = yf.Ticker(symbol)
            # Recuperiamo i dati storici (2 anni per avere 2024 e 2025 completi)
            hist = t.history(period="3y")
            
            if len(hist) > 500:
                # Calcolo Crescita 2024 (approssimativo)
                p_inizio_24 = hist['Close'].iloc[0]
                p_fine_24 = hist['Close'].iloc[252] if len(hist) > 252 else hist['Close'].iloc[-1]
                c_2024 = ((p_fine_24 - p_inizio_24) / p_inizio_24) * 100
                
                # Calcolo Crescita 2025
                p_inizio_25 = p_fine_24
                p_fine_25 = hist['Close'].iloc[-1]
                c_2025 = ((p_fine_25 - p_inizio_25) / p_inizio_25) * 100
                
                # Sentiment basato sul volume di scambi (un indicatore di feedback reale)
                vol_medio = hist['Volume'].mean()
                vol_ultimo = hist['Volume'].iloc[-1]
                feedback = "Alto" if vol_ultimo > vol_medio else "Moderato"
                
                tv_link = f"https://www.tradingview.com/symbols/{symbol}"
                
                risultati.append({
                    "Ticker": symbol,
                    "TradingView": tv_link,
                    "Feedback Mercato": feedback,
                    "Crescita 2024 (%)": round(c_2024, 2),
                    "Crescita 2025 (%)": round(c_2025, 2),
                    "Target 2026": "Espansione" if c_2025 > 0 else "Recupero",
                    "Status": "Analizzato ✅"
                })
            time.sleep(0.2) # Piccola pausa per non essere bloccati dai server
        except Exception as e:
            continue
        progresso.progress((i + 1) / len(lista_ticker))
    
    placeholder.empty()
    return pd.DataFrame(risultati)

# --- LOGICA APPLICATIVO ---
if st.button('🚀 AVVIA ANALISI DETTAGLIATA'):
    titoli = get_trending_tickers()
    if titoli:
        df_risultati = analizza_titoli(titoli)
        st.session_state.report = df_risultati
    else:
        st.error("Non è stato possibile recuperare la lista dei titoli.")

if 'report' in st.session_state:
    st.subheader("📋 Report Analisi Dettagliato")
    # Mostriamo la tabella con i dati reali
    st.dataframe(
        st.session_state.report,
        column_config={
            "TradingView": st.column_config.LinkColumn("Grafico", display_text="Apri TV 📈"),
            "Crescita 2024 (%)": st.column_config.NumberColumn(format="%.2f %%"),
            "Crescita 2025 (%)": st.column_config.NumberColumn(format="%.2f %%"),
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Download
    csv = st.session_state.report.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Salva Report CSV",
        data=csv,
        file_name=f"report_{datetime.now().strftime('%d_%m_%Y')}.csv",
        mime='text/csv'
    )
