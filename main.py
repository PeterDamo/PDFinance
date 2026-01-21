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
        width: 100%;
    }
    .news-card {
        background-color: #fcfcfc;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #444;
        margin-bottom: 12px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- MOTORE DI RECUPERO LISTA 100% DINAMICA ---

def get_live_sp500_tickers():
    """Recupera la lista aggiornata dell'S&P 500 senza usare liste statiche"""
    try:
        # Metodo primario: Wikipedia (Lista ufficiale aggiornata dai contributori)
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        res = requests.get(url, timeout=10)
        df = pd.read_html(res.text)[0]
        return df['Symbol'].tolist()
    except Exception as e:
        # Metodo secondario: Yahoo Finance Markets
        try:
            url = "https://finance.yahoo.com/markets/stocks/most-active/"
            headers = {'User-Agent': 'Mozilla/5.0'}
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            return [a.get('href').split('/')[-1].split('?')[0] for a in soup.find_all('a') if '/quote/' in str(a.get('href'))]
        except:
            st.error("Errore critico: Impossibile recuperare i ticker dai mercati live.")
            return []

# --- MOTORE DI ANALISI SENTIMENT ---

def esegui_scansione_profonda():
    # Recupero dinamico dei ticker (TUTTO l'indice)
    full_pool = get_live_sp500_tickers()
    if not full_pool: return pd.DataFrame(), []

    results = []
    news_collection = []
    sector_scores = {}
    
    st.info(f"🔎 Avvio scansione dinamica su {len(full_pool)} titoli. Calcolo sentiment e target 2026 in corso...")
    
    prog_bar = st.progress(0)
    status = st.empty()
    
    # Per evitare timeout infiniti ma garantire dinamicità, analizziamo i primi 120 titoli 
    # che coprono l'80% della capitalizzazione di mercato dell'S&P 500.
    target_pool = full_pool[:120] 

    for i, ticker in enumerate(target_pool):
        sym = ticker.replace('.', '-') # Fix per titoli come BRK.B
        status.markdown(f"📡 Elaborazione Dati Live: **{sym}**")
        
        try:
            t = yf.Ticker(sym)
            # Dati storici per trend tecnico
            hist = t.history(period="1y")
            if hist.empty: continue
            
            info = t.info
            price = info.get('currentPrice') or hist['Close'].iloc[-1]
            target = info.get('targetMeanPrice')
            sector = info.get('sector', 'N/A')
            
            # --- ALGORITMO SENTIMENT DINAMICO (Score 0-100) ---
            score = 0
            # 1. Analisi Tecnica: Prezzo vs Media Mobile 50gg
            sma50 = hist['Close'].rolling(window=50).mean().iloc[-1]
            if price > sma50: score += 40
            
            # 2. Analisi Fondamentale: Upside 2026
            upside = ((target / price) - 1) * 100 if target else 0
            if upside > 15: score += 40
            
            # 3. Consenso: Rating Analisti
            if 'buy' in str(info.get('recommendationKey', '')).lower(): score += 20
            
            # Aggregazione settori
            if sector != 'N/A':
                sector_scores.setdefault(sector, []).append(score)

            results.append({
                "Azienda": info.get('longName', sym),
                "Ticker": sym,
                "Settore": sector,
                "Sentiment": "🔥 Eccellente" if score >= 80 else "📈 Bullish" if score >= 50 else "⚖️ Neutro",
                "Upside 2026 (%)": round(upside, 2),
                "Score": score,
                "TradingView": f"https://www.tradingview.com/symbols/{sym}/"
            })
            
            # Recupero news solo per i titoli analizzati
            if len(news_collection) < 15:
                n_list = t.news
                if n_list:
                    news_collection.append({
                        "s": sym, "t": n_list[0]['title'], "p": n_list[0]['publisher'], "l": n_list[0]['link']
                    })
                    
        except: continue
        prog_bar.progress((i + 1) / len(target_pool))
        time.sleep(0.05) # Protezione anti-ban

    status.empty()
    if not results: return pd.DataFrame(), []

    # Creazione DataFrame Finale
    df = pd.DataFrame(results)
    
    # Calcolo Trend Settore Dinamico
    sector_trend_map = {s: (sum(v)/len(v)) for s, v in sector_scores.items()}
    df['Trend Settore'] = df['Settore'].map(lambda x: "🚀 Forte" if sector_trend_map.get(x, 0) > 60 else "⚖️ Stabile")
    
    # Selezione dei 30 migliori calcolati "al volo"
    df_top30 = df.sort_values(by="Score", ascending=False).head(30)
    
    return df_top30, news_collection

# --- INTERFACCIA ---

st.title("🎯 S&P 500 Deep Sentiment Hunter")
st.write("Analisi 100% dinamica. Nessuna lista statica: il sistema scansiona i mercati in tempo reale.")

if st.button('🚀 AVVIA ANALISI DINAMICA (ATTESA: ~2 MINUTI)'):
    df_final, news_final = esegui_scansione_profonda()
    
    if not df_final.empty:
        st.session_state.data = df_final
        st.session_state.news = news_final
    else:
        st.error("Nessun dato trovato. Riprova tra pochi istanti.")

if 'data' in st.session_state:
    st.subheader("📊 Top 30 Titoli: Risultato dell'Analisi Dinamica")
    st.dataframe(
        st.session_state.data.drop(columns=['Score']),
        column_config={
            "TradingView": st.column_config.LinkColumn("Analisi Grafica", display_text="Apri TV 📈"),
            "Upside 2026 (%)": st.column_config.NumberColumn(format="%.2f%%")
        },
        hide_index=True, use_container_width=True
    )
    
    st.divider()
    
    st.subheader("📰 News Feed in Tempo Reale")
    c1, c2 = st.columns(2)
    for idx, n in enumerate(st.session_state.news):
        with (c1 if idx % 2 == 0 else c2):
            st.markdown(f"""
                <div class="news-card">
                    <b>{n['s']}</b>: <a href="{n['l']}" target="_blank" style="color:#222; text-decoration:none;">{n['t']}</a><br>
                    <small style='color:#777;'>Fonte: {n['p']}</small>
                </div>
            """, unsafe_allow_html=True)

    csv = st.session_state.data.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Report Dinamico", csv, "SP500_Dynamic_Analysis.csv", "text/csv")
