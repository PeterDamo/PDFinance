import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# 1. Configurazione Pagina e Tema Chiaro
st.set_page_config(page_title="Analizzatore Finanziario 2026", layout="wide")

# CSS per sfondo bianco, tasti grigetti e TESTI GRIGIO SCURO
st.markdown("""
    <style>
    /* Sfondo principale bianco */
    .stApp {
        background-color: #ffffff;
    }
    
    /* Titoli e testi in grigio scuro */
    h1, h2, h3, span, p, .stMarkdown {
        color: #333333 !important;
    }
    
    /* Personalizzazione pulsanti (grigetto con testo scuro) */
    .stButton>button {
        background-color: #eeeeee !important;
        color: #444444 !important;
        border: 1px solid #cccccc !important;
        border-radius: 8px !important;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #e0e0e0 !important;
        border-color: #999999 !important;
    }

    /* Card delle Notizie */
    .news-card {
        background-color: #fcfcfc;
        padding: 18px;
        border-radius: 12px;
        border-left: 5px solid #666666;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .news-title { 
        font-weight: bold; 
        font-size: 1.1em; 
        color: #222222 !important; 
        display: block;
    }
    .news-text {
        color: #444444 !important;
        margin-top: 8px;
        font-size: 0.95em;
    }
    .news-meta { 
        color: #777777 !important; 
        font-size: 0.8em; 
        margin-top: 10px;
        display: block;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI CORE ---

def get_dynamic_tickers():
    """Recupera titoli attivi (USA e IT) in modo dinamico"""
    headers = {'User-Agent': 'Mozilla/5.0'}
    tickers = []
    urls = [
        "https://finance.yahoo.com/most-active",
        "https://finance.yahoo.com/markets/stocks/most-active/?lookup=MI&auto_prefill=MI"
    ]
    for url in urls:
        try:
            res = requests.get(url, headers=headers, timeout=5)
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.find_all('a'):
                href = a.get('href', '')
                if '/quote/' in href:
                    sym = href.split('/quote/')[1].split('?')[0].split('/')[0]
                    if sym not in tickers: tickers.append(sym)
        except: continue
    
    # Fallback se lo scraping fallisce
    if len(tickers) < 5:
        tickers = ['NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'ENEL.MI', 'ISP.MI', 'UCG.MI', 'RACE.MI', 'ASML']
    return tickers[:30]

def esegui_analisi():
    pool = get_dynamic_tickers()
    data_list = []
    news_list = []
    
    progresso = st.progress(0)
    status = st.empty()

    for i, symbol in enumerate(pool):
        status.markdown(f"<span style='color:#444'>Analisi in corso: **{symbol}**...</span>", unsafe_allow_html=True)
        try:
            t = yf.Ticker(symbol)
            # Carichiamo lo storico per i calcoli 2024-2025
            hist = t.history(start="2024-01-01")
            
            if not hist.empty:
                info = t.info
                name = info.get('longName', symbol)
                sector = info.get('sector', 'N/A')
                
                # Calcolo Crescita Storica
                df_24 = hist.loc['2024-01-01':'2024-12-31']['Close']
                c24 = ((df_24.iloc[-1] / df_24.iloc[0]) - 1) * 100 if not df_24.empty else 0
                
                df_25 = hist.loc['2025-01-01':'2025-12-31']['Close']
                c25 = ((df_25.iloc[-1] / df_25.iloc[0]) - 1) * 100 if not df_25.empty else 0
                
                # Crescita Prevista 2026 (Target Analisti)
                p_curr = info.get('currentPrice', hist['Close'].iloc[-1])
                p_targ = info.get('targetMeanPrice')
                c26_prev = ((p_targ / p_curr) - 1) * 100 if p_targ else 0
                
                data_list.append({
                    "Azienda": name,
                    "Ticker": symbol,
                    "Settore": sector,
                    "Crescita 2024 (%)": round(c24, 2),
                    "Crescita 2025 (%)": round(c25, 2),
                    "Prevista 2026 (%)": round(c26_prev, 2),
                    "Analisi": f"https://www.tradingview.com/symbols/{symbol}"
                })

                # Recupero News (Metodo Rinforzato)
                raw_news = t.news
                if raw_news:
                    n = raw_news[0]
                    news_list.append({
                        "name": name,
                        "ticker": symbol,
                        "title": n.get('title', 'Titolo non disponibile'),
                        "publisher": n.get('publisher', 'Fonte Finanziaria'),
                        "time": datetime.fromtimestamp(n.get('providerPublishTime')).strftime('%d/%m/%Y %H:%M')
                    })
            
            time.sleep(0.1)
        except: continue
        progresso.progress((i + 1) / len(pool))
    
    status.empty()
    df = pd.DataFrame(data_list).sort_values(by="Prevista 2026 (%)", ascending=False).head(20)
    return df, news_list

# --- INTERFACCIA UTENTE ---

st.title("🏹 Market Insight 2026")
st.write("Scanner dinamico per titoli e ETF con analisi storica e news feed.")

if st.button('🚀 AVVIA SCANSIONE MERCATI'):
    df_res, news_res = esegui_analisi()
    st.session_state.df = df_res
    st.session_state.news = news_res

if 'df' in st.session_state:
    st.subheader("📊 Top 20 Titoli per Potenziale 2026")
    st.dataframe(
        st.session_state.df,
        column_config={
            "Analisi": st.column_config.LinkColumn("Grafico", display_text="Apri TV 📈"),
            "Crescita 2024 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Crescita 2025 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Prevista 2026 (%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
        hide_index=True, use_container_width=True
    )
    
    # Download CSV
    csv = st.session_state.df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Report CSV", csv, "analisi_finanza_2026.csv", "text/csv")

    st.divider()

    st.subheader("📰 Ultime Notizie dai Mercati Analizzati")
    if st.session_state.news:
        c1, c2 = st.columns(2)
        for idx, n in enumerate(st.session_state.news):
            with (c1 if idx % 2 == 0 else c2):
                st.markdown(f"""
                    <div class="news-card">
                        <span class="news-title">{n['name']} ({n['ticker']})</span>
                        <p class="news-text">{n['title']}</p>
                        <span class="news-meta"><b>{n['publisher']}</b> • {n['time']}</span>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Nessuna notizia recente trovata per i titoli selezionati.")
