import streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime
import time

# Configurazione Pagina
st.set_page_config(page_title="Finanza 2026 Pro", layout="wide")

# CSS per forzare lo sfondo chiaro e lo stile moderno
st.markdown("""
    <style>
    /* Sfondo principale chiaro */
    .stApp {
        background-color: #ffffff;
    }
    /* Stile per le card delle notizie */
    .news-card {
        background-color: #f1f3f5;
        padding: 15px;
        border-radius: 10px;
        border-left: 6px solid #007bff;
        margin-bottom: 12px;
        color: #1f1f1f;
    }
    .news-title { font-weight: bold; font-size: 1.1em; display: block; margin-bottom: 5px; }
    .news-date { color: #6c757d; font-size: 0.85em; }
    
    /* Titoli neri per massima leggibilità */
    h1, h2, h3, p {
        color: #1f1f1f !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📈 Analisi Finanziaria 2026")
st.write("Monitoraggio dinamico di titoli e ETF con analisi del sentiment e news.")

def get_data_and_news(tickers):
    results = []
    news_list = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for i, symbol in enumerate(tickers):
        status_text.text(f"Analisi in corso: {symbol}...")
        try:
            t = yf.Ticker(symbol)
            info = t.info
            name = info.get('longName', symbol) # Recupera il nome completo o usa il ticker se manca
            
            hist = t.history(period="3y")
            if not hist.empty:
                # Calcolo crescita (2024 vs 2025)
                c_2024 = ((hist['Close'].iloc[252] / hist['Close'].iloc[0]) - 1) * 100 if len(hist) > 252 else 0
                c_2025 = ((hist['Close'].iloc[-1] / hist['Close'].iloc[252]) - 1) * 100 if len(hist) > 252 else 0
                
                results.append({
                    "Azienda": name,
                    "Ticker": symbol,
                    "TradingView": f"https://www.tradingview.com/symbols/{symbol}",
                    "Crescita 2024 (%)": round(c_2024, 2),
                    "Crescita 2025 (%)": round(c_2025, 2),
                    "Sentiment": "Bullish 🚀" if c_2025 > 5 else "Stabile ⚖️"
                })
                
                # News
                if t.news:
                    n = t.news[0]
                    news_list.append({
                        "ticker": symbol,
                        "name": name,
                        "title": n['title'],
                        "publisher": n['publisher'],
                        "date": datetime.fromtimestamp(n['providerPublishTime']).strftime('%d/%m/%Y %H:%M')
                    })
            
            time.sleep(0.1)
            progress_bar.progress((i + 1) / len(tickers))
        except:
            continue
            
    status_text.empty()
    return pd.DataFrame(results), news_list

# --- INTERFACCIA ---
if st.button('🔄 AVVIA SCANSIONE DINAMICA'):
    # Lista di test (20 titoli tra i più cercati)
    trending = ['NVDA', 'TSLA', 'AAPL', 'MSFT', 'AMZN', 'META', 'GOOGL', 'ENEL.MI', 'ISP.MI', 'UCG.MI', 
                'PYPL', 'INTC', 'ASML', 'NVO', 'SHEL', 'AMD', 'NFLX', 'V', 'JPM', 'IE00B4L5Y983']
    
    df, news = get_data_and_news(trending)
    st.session_state.df = df
    st.session_state.news = news

if 'df' in st.session_state:
    st.subheader("📊 Tabella Analisi 2026")
    st.dataframe(
        st.session_state.df,
        column_config={
            "TradingView": st.column_config.LinkColumn("Analisi", display_text="Grafico 📈"),
            "Crescita 2024 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Crescita 2025 (%)": st.column_config.NumberColumn(format="%.2f%%")
        },
        hide_index=True, use_container_width=True
    )
    
    # Download CSV
    csv_data = st.session_state.df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Report CSV", csv_data, f"Analisi_{datetime.now().strftime('%Y%m%d')}.csv", "text/csv")

    st.markdown("---")
    st.subheader("📰 Ultime Notizie dai Mercati")
    
    col1, col2 = st.columns(2)
    for idx, item in enumerate(st.session_state.news):
        with (col1 if idx % 2 == 0 else col2):
            st.markdown(f"""
                <div class="news-card">
                    <span class="news-title">{item['name']} ({item['ticker']})</span>
                    <p style='margin: 0;'>{item['title']}</p>
                    <span class="news-date">Fonte: {item['publisher']} | Data: {item['date']}</span>
                </div>
                """, unsafe_allow_html=True)
