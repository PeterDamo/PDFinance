import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import random

# 1. Configurazione UI
st.set_page_config(page_title="Sentiment Hunter 2026", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .news-card {
        background-color: #f8f9fa;
        padding: 12px;
        border-radius: 8px;
        border-left: 5px solid #1f77b4;
        margin-bottom: 10px;
    }
    .stButton>button {
        background-color: #000000;
        color: white;
        font-weight: bold;
        width: 100%;
        border-radius: 10px;
        height: 3em;
    }
    </style>
    """, unsafe_allow_html=True)

# --- MOTORE DI RECUPERO TICKER (100% DINAMICO) ---
def get_dynamic_tickers():
    """Recupera titoli dai 'Most Active' di Yahoo e dall'indice S&P 500"""
    tickers = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    
    try:
        # Sorgente 1: Wikipedia S&P 500
        url_sp = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        df_sp = pd.read_html(requests.get(url_sp, headers=headers).text)[0]
        tickers.extend(df_sp['Symbol'].tolist())
    except: pass

    try:
        # Sorgente 2: Yahoo Finance Most Active (Sentiment di mercato attuale)
        url_y = "https://finance.yahoo.com/markets/stocks/most-active/"
        res = requests.get(url_y, headers=headers)
        soup = BeautifulSoup(res.text, 'html.parser')
        for a in soup.find_all('a'):
            href = str(a.get('href'))
            if '/quote/' in href:
                t = href.split('/')[-1].split('?')[0]
                if t.isalpha() and len(t) < 6: tickers.append(t)
    except: pass
    
    return list(set(tickers)) # Rimuove duplicati

# --- MOTORE DI ANALISI SENTIMENT & NEWS ---
def run_deep_analysis():
    raw_tickers = get_dynamic_tickers()
    # Analizziamo un pool di 100 titoli freschi per trovare i 30 migliori
    pool = random.sample(raw_tickers, min(len(raw_tickers), 100))
    
    results = []
    news_feed = []
    sector_data = {}

    progress_bar = st.progress(0)
    status = st.empty()
    
    session = requests.Session()
    session.headers.update({'User-Agent': 'Mozilla/5.0'})

    for i, ticker in enumerate(pool):
        symbol = ticker.replace('.', '-')
        status.info(f"🔍 Analisi Sentiment & News: {symbol} ({i+1}/{len(pool)})")
        
        try:
            t = yf.Ticker(symbol, session=session)
            hist = t.history(period="1y")
            if hist.empty: continue
            
            info = t.info
            price = info.get('currentPrice') or hist['Close'].iloc[-1]
            target = info.get('targetMeanPrice')
            sector = info.get('sector', 'N/A')
            
            # --- CALCOLO SENTIMENT SCORE (DINAMICO) ---
            score = 0
            
            # 1. Sentiment Tecnico (Trend)
            sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            if price > sma50: score += 35
            
            # 2. Sentiment Fondamentale (Analisti)
            upside = ((target / price) - 1) * 100 if target else 0
            if upside > 15: score += 40
            
            # 3. Sentiment di Mercato (Rating)
            rec = str(info.get('recommendationKey', '')).lower()
            if 'buy' in rec: score += 25
            
            # News Processing
            ticker_news = t.news
            if ticker_news:
                for n in ticker_news[:1]:
                    news_feed.append({'s': symbol, 't': n['title'], 'l': n['link'], 'p': n['publisher']})
            
            # Raccolta per andamento settore
            if sector != 'N/A':
                sector_data.setdefault(sector, []).append(score)

            results.append({
                "Azienda": info.get('longName', symbol),
                "Ticker": symbol,
                "Settore": sector,
                "Prezzo Attuale": f"${price:.2f}",
                "Potenziale 2026 (%)": round(upside, 2),
                "Sentiment Score": score,
                "Rating": "💎 ECCELLENTE" if score >= 85 else "📈 PROMETTENTE" if score >= 55 else "⚖️ NEUTRO",
                "TradingView": f"https://www.tradingview.com/symbols/{symbol}/"
            })
            
            time.sleep(0.1) # Evita blocchi IP
        except:
            continue
        progress_bar.progress((i + 1) / len(pool))

    # Calcolo Andamento Settore
    df = pd.DataFrame(results)
    if df.empty: return df, []
    
    sector_trend = {s: (sum(v)/len(v)) for s, v in sector_data.items()}
    df['Andamento Settore'] = df['Settore'].map(lambda x: "🚀 Forte" if sector_trend.get(x, 0) > 60 else "⚖️ Stabile")
    
    # Selezione finale Top 30
    df_final = df.sort_values(by="Sentiment Score", ascending=False).head(30)
    return df_final, news_feed

# --- INTERFACCIA UTENTE ---
st.title("🎯 Sentiment Hunter: Top 30 Opportunità 2026")
st.write("L'analisi è **100% dinamica**: i titoli vengono estratti dai mercati e analizzati solo al click del pulsante.")

if st.button('🚀 AVVIA SCANSIONE MERCATI E SENTIMENT NEWS'):
    data, news = run_deep_analysis()
    if not data.empty:
        st.session_state.data = data
        st.session_state.news = news
    else:
        st.error("Nessun dato recuperato. Riprova tra un istante.")

if 'data' in st.session_state:
    # Tabella Risultati
    st.subheader("📊 Classifica dei 30 Titoli con Maggiore Sentiment")
    st.dataframe(
        st.session_state.data.drop(columns=['Sentiment Score']),
        column_config={
            "TradingView": st.column_config.LinkColumn("Grafico", display_text="Live 📈"),
            "Potenziale 2026 (%)": st.column_config.NumberColumn(format="%.2f%%")
        },
        hide_index=True, use_container_width=True
    )
    
    # Download
    csv = st.session_state.data.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Tabella Analisi (CSV)", csv, "sentiment_analysis_2026.csv", "text/csv")

    st.divider()

    # Sezione News
    st.subheader("📰 Feed News & Post Correlati")
    col1, col2 = st.columns(2)
    for i, n in enumerate(st.session_state.news[:20]):
        with (col1 if i % 2 == 0 else col2):
            st.markdown(f"""
                <div class="news-card">
                    <small><b>{n['s']}</b> | {n['p']}</small><br>
                    <a href="{n['l']}" target="_blank" style="text-decoration:none; color:#1f77b4; font-weight:bold;">{n['t']}</a>
                </div>
            """, unsafe_allow_html=True)
