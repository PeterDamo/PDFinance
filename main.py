import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

# 1. Configurazione Pagina
st.set_page_config(page_title="Sentiment Scanner 2026 Pro", layout="wide")

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
    </style>
    """, unsafe_allow_html=True)

# --- FUNZIONI DI CALCOLO SICURE ---

def calcola_sentiment(hist, info):
    score = 0
    try:
        # Usiamo .get() per evitare KeyError su info
        current_price = info.get('currentPrice') or info.get('regularMarketPrice') or hist['Close'].iloc[-1]
        
        # 1. Trend (Prezzo vs Media 50gg)
        if len(hist) >= 50:
            sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            if current_price > sma50: score += 40
        
        # 2. Analyst Upside
        target = info.get('targetMeanPrice')
        if target and target > current_price: score += 40
        
        # 3. Volume Momentum
        avg_vol = info.get('averageVolume', 1)
        curr_vol = info.get('volume', 0)
        if curr_vol > avg_vol: score += 20
        
        if score >= 80: return score, "Strong Buy 💎"
        if score >= 50: return score, "Bullish 📈"
        if score >= 30: return score, "Neutral ⚖️"
        return score, "Wait & Watch ⏳"
    except:
        return 0, "Analisi parziale ⚠️"

def esegui_analisi_robusta():
    # Recupero ticker dinamici (Metodo semplificato per stabilità)
    headers = {'User-Agent': 'Mozilla/5.0'}
    pool = []
    try:
        res = requests.get("https://finance.yahoo.com/most-active", headers=headers, timeout=5)
        soup = BeautifulSoup(res.text, 'html.parser')
        for a in soup.find_all('a'):
            href = a.get('href', '')
            if '/quote/' in href:
                sym = href.split('/quote/')[1].split('?')[0].split('/')[0]
                if sym.isalpha() and len(sym) < 6 and sym not in pool: pool.append(sym)
    except: pass
    
    if len(pool) < 5: pool = ['NVDA', 'AAPL', 'TSLA', 'MSFT', 'ENEL.MI', 'ISP.MI', 'UCG.MI']
    
    data_list = []
    news_list = []
    progresso = st.progress(0)
    status = st.empty()

    for i, symbol in enumerate(pool[:25]):
        status.markdown(f"<span style='color:#444'>Analisi in corso: **{symbol}**...</span>", unsafe_allow_html=True)
        try:
            t = yf.Ticker(symbol)
            hist = t.history(period="3y") # Scarichiamo un blocco dati ampio
            
            if not hist.empty and len(hist) > 200:
                info = t.info
                
                # --- CALCOLO CRESCITA ANNUALE (SICURO) ---
                # Invece di loc['data'], filtriamo per anno e prendiamo primo/ultimo record
                hist_24 = hist[hist.index.year == 2024]
                c24 = ((hist_24['Close'].iloc[-1] / hist_24['Close'].iloc[0]) - 1) * 100 if not hist_24.empty else 0
                
                hist_25 = hist[hist.index.year == 2025]
                c25 = ((hist_25['Close'].iloc[-1] / hist_25['Close'].iloc[0]) - 1) * 100 if not hist_25.empty else 0
                
                # Sentiment
                score, label = calcola_sentiment(hist, info)
                
                data_list.append({
                    "Azienda": info.get('longName', symbol),
                    "Ticker": symbol,
                    "Sentiment": label,
                    "Score": score,
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
                        "time": datetime.fromtimestamp(n.get('providerPublishTime')).strftime('%d/%m/%Y')
                    })
            time.sleep(0.1)
        except Exception as e:
            continue # Se un titolo fallisce, passa al prossimo senza crashare
        progresso.progress((i + 1) / len(pool[:25]))
    
    status.empty()
    df = pd.DataFrame(data_list).sort_values(by="Score", ascending=False).head(20)
    return df, news_list

# --- UI ---
st.title("🏹 Market Sentiment 2026")

if st.button('🚀 SCANSIONE E CLASSIFICA SENTIMENT'):
    df_res, news_res = esegui_analisi_robusta()
    st.session_state.df = df_res
    st.session_state.news = news_res

if 'df' in st.session_state:
    st.subheader("📊 Classifica Top 20 per Sentiment")
    st.dataframe(
        st.session_state.df.drop(columns=['Score']),
        column_config={"Analisi": st.column_config.LinkColumn("Grafico", display_text="Apri TV 📈")},
        hide_index=True, use_container_width=True
    )

    st.divider()
    st.subheader("📰 Ultime Notizie dai Leader")
    if st.session_state.news:
        c1, c2 = st.columns(2)
        for idx, n in enumerate(st.session_state.news[:14]):
            with (c1 if idx % 2 == 0 else c2):
                st.markdown(f"""<div class="news-card"><b>{n['name']}</b><br>{n['title']}<br><small>{n['publisher']} • {n['time']}</small></div>""", unsafe_allow_html=True)
