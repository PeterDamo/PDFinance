import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# 1. Configurazione Pagina
st.set_page_config(page_title="Sentiment Scanner 2026", layout="wide")

# CSS per stile Moderno, Sfondo Bianco e Testi Grigio Scuro
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3, span, p, .stMarkdown { color: #333333 !important; }
    
    .stButton>button {
        background-color: #eeeeee !important;
        color: #444444 !important;
        border: 1px solid #cccccc !important;
        border-radius: 8px !important;
        font-weight: 600;
    }
    
    .news-card {
        background-color: #fcfcfc;
        padding: 18px;
        border-radius: 12px;
        border-left: 5px solid #444444;
        margin-bottom: 15px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .news-title { font-weight: bold; color: #222222 !important; display: block; }
    .news-meta { color: #777777 !important; font-size: 0.8em; margin-top: 10px; display: block; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI DI CALCOLO ---

def calcola_sentiment(hist, info):
    """Calcola un punteggio di sentiment da 0 a 100"""
    score = 0
    try:
        current_price = info.get('currentPrice', hist['Close'].iloc[-1])
        # 1. Trend (Prezzo vs Media 50gg)
        sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
        if current_price > sma50: score += 40
        
        # 2. Analyst Upside
        target = info.get('targetMeanPrice')
        if target and target > current_price: score += 40
        
        # 3. Volume Momentum
        avg_vol = info.get('averageVolume', 1)
        curr_vol = info.get('volume', 0)
        if curr_vol > avg_vol: score += 20
        
        # Classificazione
        if score >= 80: return score, "Strong Buy 💎"
        if score >= 50: return score, "Bullish 📈"
        if score >= 30: return score, "Neutral ⚖️"
        return score, "Wait & Watch ⏳"
    except:
        return 0, "N/A"

def get_dynamic_tickers():
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
    if len(tickers) < 5:
        tickers = ['NVDA', 'AAPL', 'TSLA', 'MSFT', 'AMZN', 'ENEL.MI', 'ISP.MI', 'UCG.MI']
    return tickers[:30]

def esegui_analisi():
    pool = get_dynamic_tickers()
    data_list = []
    news_list = []
    progresso = st.progress(0)
    status = st.empty()

    for i, symbol in enumerate(pool):
        status.markdown(f"<span style='color:#444'>Analisi Sentiment: **{symbol}**...</span>", unsafe_allow_html=True)
        try:
            t = yf.Ticker(symbol)
            hist = t.history(start="2024-01-01")
            if not hist.empty:
                info = t.info
                # Calcoli Crescita
                c24 = ((hist.loc['2024-12-31']['Close'].iloc[0] / hist.loc['2024-01-01']['Close'].iloc[0]) - 1) * 100
                c25 = ((hist.loc['2025-12-31']['Close'].iloc[0] / hist.loc['2025-01-01']['Close'].iloc[0]) - 1) * 100
                
                # Calcolo Sentiment
                score, label = calcola_sentiment(hist, info)
                
                data_list.append({
                    "Azienda": info.get('longName', symbol),
                    "Ticker": symbol,
                    "Sentiment": label,
                    "Sentiment Score": score,
                    "Crescita 2024 (%)": round(c24, 2),
                    "Crescita 2025 (%)": round(c25, 2),
                    "Analisi": f"https://www.tradingview.com/symbols/{symbol}"
                })

                if t.news:
                    n = t.news[0]
                    news_list.append({
                        "name": info.get('longName', symbol),
                        "ticker": symbol,
                        "title": n.get('title'),
                        "publisher": n.get('publisher'),
                        "time": datetime.fromtimestamp(n.get('providerPublishTime')).strftime('%d/%m/%Y %H:%M')
                    })
            time.sleep(0.1)
        except: continue
        progresso.progress((i + 1) / len(pool))
    
    status.empty()
    # Classificazione: Ordiniamo per Sentiment Score decrescente
    df = pd.DataFrame(data_list).sort_values(by="Sentiment Score", ascending=False).head(20)
    return df, news_list

# --- INTERFACCIA ---

st.title("🏹 Market Sentiment 2026")
st.write("Classifica dinamica basata su analisi tecnica, volumi e rating analisti.")

if st.button('🚀 SCANSIONE E CLASSIFICA SENTIMENT'):
    df_res, news_res = esegui_analisi()
    st.session_state.df = df_res
    st.session_state.news = news_res

if 'df' in st.session_state:
    st.subheader("📊 Classifica Top 20 per Sentiment")
    st.dataframe(
        st.session_state.df.drop(columns=['Sentiment Score']), # Nascondiamo il punteggio numerico
        column_config={"Analisi": st.column_config.LinkColumn("Dettagli 📈")},
        hide_index=True, use_container_width=True
    )
    
    # Salvataggio Locale con Data
    data_oggi = datetime.now().strftime("%Y-%m-%d")
    csv = st.session_state.df.to_csv(index=False).encode('utf-8')
    st.download_button(f"📥 Salva Report {data_oggi}", csv, f"Report_Sentiment_{data_oggi}.csv", "text/csv")

    st.divider()
    st.subheader("📰 Notizie dai Titoli Leader")
    if st.session_state.news:
        c1, c2 = st.columns(2)
        for idx, n in enumerate(st.session_state.news[:14]):
            with (c1 if idx % 2 == 0 else c2):
                st.markdown(f"""
                    <div class="news-card">
                        <span class="news-title">{n['name']} ({n['ticker']})</span>
                        <p style='color:#444'>{n['title']}</p>
                        <span class="news-meta"><b>{n['publisher']}</b> • {n['time']}</span>
                    </div>
                """, unsafe_allow_html=True)
