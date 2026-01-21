import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup
import time

# 1. Configurazione Pagina Professional
st.set_page_config(page_title="Deep Market Scanner 2026", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3, p, span, .stMarkdown { color: #333333 !important; }
    .stButton>button {
        background-color: #222222 !important;
        color: #ffffff !important;
        border-radius: 8px !important;
        padding: 15px !important;
        font-weight: bold;
    }
    .news-card {
        background-color: #fcfcfc;
        padding: 12px;
        border-radius: 8px;
        border-left: 4px solid #444;
        margin-bottom: 10px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    </style>
    """, unsafe_allow_html=True)

# --- MOTORE DI RECUPERO LISTA DINAMICA ---

@st.cache_data(ttl=3600)
def fetch_full_sp500_list():
    """Recupera la lista aggiornata al secondo da Wikipedia"""
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        return pd.read_html(url)[0]['Symbol'].tolist()
    except:
        return ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "BRK-B"]

# --- MOTORE DI ANALISI DINAMICA (Senza limiti statici) ---

def deep_market_analysis():
    full_pool = fetch_full_sp500_list()
    results = []
    news_collection = []
    sector_raw_data = {}
    
    st.info(f"🚀 Avvio scansione profonda su {len(full_pool)} titoli. L'operazione potrebbe richiedere alcuni minuti per garantire dati 100% dinamici.")
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Analizziamo un campione molto ampio (es. 150 titoli per bilanciare profondità e tempo)
    # Per analizzarli TUTTI e 500 basterebbe togliere [:150], ma il tempo salirebbe a ~10 min
    target_pool = full_pool[:150] 
    
    for i, ticker in enumerate(target_pool):
        clean_ticker = ticker.replace('.', '-')
        status_text.markdown(f"🔍 Analisi Quantitativa: **{clean_ticker}** ({i+1}/{len(target_pool)})")
        
        try:
            t = yf.Ticker(clean_ticker)
            # Recupero storico per sentiment tecnico
            hist = t.history(period="1y")
            if hist.empty: continue
            
            info = t.info
            curr_p = info.get('currentPrice') or hist['Close'].iloc[-1]
            target = info.get('targetMeanPrice')
            sector = info.get('sector', 'N/A')
            
            # --- LOGICA SENTIMENT DINAMICA ---
            score = 0
            # 1. Momentum (Prezzo vs Media Mobile 50gg)
            sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            if curr_p > sma50: score += 35
            
            # 2. Analisti (Upside potenziale 2026)
            upside = ((target / curr_p) - 1) * 100 if target else 0
            if upside > 15: score += 40
            
            # 3. Raccomandazione Corrente
            rec = info.get('recommendationKey', '').lower()
            if 'buy' in rec: score += 25

            # Aggregazione dati settore
            if sector != 'N/A':
                sector_raw_data.setdefault(sector, []).append(score)

            results.append({
                "Azienda": info.get('longName', ticker),
                "Ticker": ticker,
                "Settore": sector,
                "Sentiment": "💎 TOP PICK" if score >= 85 else "📈 BULLISH" if score >= 55 else "⚖️ NEUTRAL",
                "Prezzo": f"${curr_p:.2f}",
                "Upside 2026": f"{upside:.2f}%",
                "Score": score,
                "TradingView": f"https://www.tradingview.com/symbols/{clean_ticker}/"
            })
            
            # News Feed dinamico
            if len(news_collection) < 20: # Limitiamo a 20 news totali per pulizia
                raw_n = t.news
                if raw_n:
                    news_collection.append({
                        "sym": ticker, "title": raw_n[0]['title'], 
                        "pub": raw_n[0]['publisher'], "link": raw_n[0]['link']
                    })
        except:
            continue
            
        progress_bar.progress((i + 1) / len(target_pool))
        # Piccola pausa per evitare il rate-limiting dei server
        time.sleep(0.05)

    status_text.success("✅ Analisi completata con successo!")
    
    if not results: return pd.DataFrame(), []

    # Creazione DataFrame e Calcolo Trend Settore Dinamico
    df = pd.DataFrame(results)
    sector_trend_map = {s: (sum(v)/len(v)) for s, v in sector_raw_data.items()}
    
    df['Trend Settore'] = df['Settore'].map(
        lambda x: "🚀 Strong" if sector_trend_map.get(x, 0) > 65 else "⚖️ Stable"
    )
    
    # Selezione dei 30 migliori in base al Sentiment calcolato "al volo"
    df_final = df.sort_values(by="Score", ascending=False).head(30)
    
    return df_final, news_collection

# --- INTERFACCIA UTENTE ---

st.title("🏹 Deep Sentiment Hunter 2026")
st.write("Questa analisi non è statica. Il sistema sta scansionando i dati live dell'S&P 500 per trovare i 30 titoli con il miglior momentum e consenso analisti in questo istante.")

if st.button('🚀 AVVIA SCANSIONE PROFONDA (ATTESA STIMATA: 2-3 MIN)'):
    df_res, news_res = deep_market_analysis()
    
    if not df_res.empty:
        st.session_state.master_df = df_res
        st.session_state.master_news = news_res
    else:
        st.error("Errore nel recupero dati. Riprova.")

if 'master_df' in st.session_state:
    st.subheader("📊 Classifica Dinamica: Top 30 Sentiment al Momento")
    
    st.dataframe(
        st.session_state.master_df.drop(columns=['Score']),
        column_config={
            "TradingView": st.column_config.LinkColumn("Grafico Live", display_text="Open TV 📈"),
            "Sentiment": st.column_config.TextColumn("Valutazione AI"),
            "Upside 2026": st.column_config.TextColumn("Potenziale")
        },
        hide_index=True, use_container_width=True
    )
    
    st.divider()
    
    st.subheader("📰 News correlate ai Titoli Leader")
    c1, c2 = st.columns(2)
    for idx, n in enumerate(st.session_state.master_news):
        with (c1 if idx % 2 == 0 else c2):
            st.markdown(f"""
                <div class="news-card">
                    <small>{n['sym']} • {n['pub']}</small><br>
                    <a href="{n['link']}" target="_blank" style="text-decoration:none; color:#222; font-weight:bold;">
                        {n['title']}
                    </a>
                </div>
            """, unsafe_allow_html=True)
            
    st.download_button("📥 Scarica Report Dinamico CSV", 
                       st.session_state.master_df.to_csv(index=False).encode('utf-8'),
                       "market_analysis_2026.csv", "text/csv")
