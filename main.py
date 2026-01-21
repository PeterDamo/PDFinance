import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# Configurazione Tema e Pagina
st.set_page_config(page_title="Finanza 2026 Pro", layout="wide", initial_sidebar_state="collapsed")

# CSS personalizzato per uno stile moderno e chiaro
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 20px; height: 3em; background-color: #007bff; color: white; }
    .news-card { background-color: white; padding: 15px; border-radius: 10px; border-left: 5px solid #007bff; margin-bottom: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    .news-date { color: #6c757d; font-size: 0.85em; }
    .news-title { font-weight: bold; color: #1f1f1f; }
    </style>
    """, unsafe_allow_stdio=True)

st.title("📈 Analisi Finanziaria 2026")
st.caption("Focus su titoli sottovalutati, espansione di mercato e sentiment in tempo reale.")

# --- FUNZIONE RECUPERO DATI E NEWS ---
def get_data_and_news(tickers):
    results = []
    news_list = []
    
    progress_bar = st.progress(0)
    for i, symbol in enumerate(tickers):
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="3y")
            
            if not hist.empty:
                # Calcolo crescita (2024 e 2025)
                c_2024 = ((hist['Close'].iloc[252] / hist['Close'].iloc[0]) - 1) * 100 if len(hist) > 252 else 0
                c_2025 = ((hist['Close'].iloc[-1] / hist['Close'].iloc[252]) - 1) * 100 if len(hist) > 252 else 0
                
                results.append({
                    "Ticker": symbol,
                    "TradingView": f"https://www.tradingview.com/symbols/{symbol}",
                    "Crescita 2024 (%)": round(c_2024, 2),
                    "Crescita 2025 (%)": round(c_2025, 2),
                    "Sentiment": "Bullish" if c_2025 > 0 else "Neutral"
                })
                
                # Recupero ultima notizia
                ticker_news = t.news
                if ticker_news:
                    last_news = ticker_news[0]
                    # Conversione data unix in leggibile
                    dt_object = datetime.fromtimestamp(last_news['providerPublishTime'])
                    news_list.append({
                        "ticker": symbol,
                        "title": last_news['title'],
                        "publisher": last_news['publisher'],
                        "date": dt_object.strftime('%d %b %Y, %H:%M')
                    })
            
            time.sleep(0.1)
            progress_bar.progress((i + 1) / len(tickers))
        except:
            continue
            
    return pd.DataFrame(results), news_list

# --- INTERFACCIA ---
if st.button('🔄 Avvia Scansione Mercati e News'):
    # Lista dinamica (usiamo una selezione dei più attivi per stabilità)
    trending = ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'AMZN', 'META', 'GOOGL', 'BRK-B', 'LLY', 'AVGO', 
                'V', 'JPM', 'ENEL.MI', 'ISP.MI', 'UCG.MI', 'PYPL', 'INTC', 'ASML', 'NVO', 'SHEL']
    
    df, news = get_data_and_news(trending)
    st.session_state.df = df
    st.session_state.news = news

if 'df' in st.session_state:
    # 1. Tabella Principale
    st.subheader("📊 Analisi Titoli Selezionati")
    st.dataframe(
        st.session_state.df,
        column_config={
            "TradingView": st.column_config.LinkColumn("Grafico", display_text="Dettagli 📈")
        },
        hide_index=True, use_container_width=True
    )
    
    # Pulsante di Download posizionato bene
    csv = st.session_state.df.to_csv(index=False).encode('utf-8')
    st.download_button("💾 Salva Report CSV", csv, f"Report_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

    st.divider()

    # 2. Sezione News Feed
    st.subheader("📰 Ultime Notizie e Sentiment")
    
    col1, col2 = st.columns(2)
    for idx, item in enumerate(st.session_state.news):
        with (col1 if idx % 2 == 0 else col2):
            st.markdown(f"""
                <div class="news-card">
                    <span class="news-title">{item['ticker']} - {item['title']}</span><br>
                    <span class="news-date">Fonte: {item['publisher']} | Data: {item['date']}</span>
                </div>
                """, unsafe_allow_stdio=True)
