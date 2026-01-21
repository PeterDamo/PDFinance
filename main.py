import streamlit as st
import yfinance as yf
import pandas as pd
import requests
from bs4 import BeautifulSoup

# 1. Configurazione Pagina
st.set_page_config(page_title="S&P 500 Hunter 2026", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3, p, span, .stMarkdown { color: #333333 !important; }
    .stButton>button {
        background-color: #eeeeee !important;
        color: #444444 !important;
        border: 1px solid #cccccc !important;
        border-radius: 8px !important;
        font-weight: 600;
        width: 100%;
    }
    .news-card {
        background-color: #f9f9f9;
        padding: 15px;
        border-radius: 12px;
        border-left: 6px solid #444444;
        margin-bottom: 12px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

# --- RECUPERO TITOLI DINAMICO ---

def get_sp500_dynamic():
    try:
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        tables = pd.read_html(url)
        return tables[0]['Symbol'].tolist()
    except Exception:
        # Fallback se Wikipedia non risponde
        return ['AAPL', 'MSFT', 'NVDA', 'GOOGL', 'AMZN', 'META', 'TSLA', 'AVGO', 'BRK-B', 'LLY']

# --- ANALISI CORE ---

def esegui_analisi():
    all_tickers = get_sp500_dynamic()
    results = []
    news_feed = []
    sector_scores = {}
    
    # Pool di analisi (limitato a 60 per stabilità e velocità)
    pool = all_tickers[:60] 
    status = st.empty()
    bar = st.progress(0)
    
    for i, sym in enumerate(pool):
        status.markdown(f"<span style='color:#444'>Analisi: **{sym}**...</span>", unsafe_allow_html=True)
        try:
            clean_sym = sym.replace('.', '-')
            t = yf.Ticker(clean_sym)
            hist = t.history(period="2y") 
            
            if hist.empty or len(hist) < 20:
                continue
            
            info = t.info
            curr_p = info.get('currentPrice') or hist['Close'].iloc[-1]
            target = info.get('targetMeanPrice')
            sector = info.get('sector', 'N/A')
            
            # Calcolo Crescite (Evitiamo date fisse per prevenire KeyError)
            h24 = hist[hist.index.year == 2024]
            c24 = ((h24['Close'].iloc[-1] / h24['Close'].iloc[0]) - 1) * 100 if len(h24) > 1 else 0
            
            h25 = hist[hist.index.year == 2025]
            c25 = ((h25['Close'].iloc[-1] / h25['Close'].iloc[0]) - 1) * 100 if len(h25) > 1 else 0
            
            upside_26 = ((target / curr_p) - 1) * 100 if target else 0
            
            # Sentiment Score Algoritmico
            score = 0
            sma50 = hist['Close'].rolling(window=50).mean().iloc[-1] if len(hist) >= 50 else curr_p
            if curr_p > sma50: score += 40
            if upside_26 > 10: score += 40
            if info.get('recommendationKey') in ['buy', 'strong_buy']: score += 20
            
            # Track Settore
            if sector != 'N/A':
                sector_scores.setdefault(sector, []).append(score)

            results.append({
                "Azienda": info.get('longName', sym),
                "Ticker": sym,
                "Settore": sector,
                "Sentiment": "🔥 Eccellente" if score >= 80 else "📈 Bullish" if score >= 50 else "⚖️ Neutro",
                "Crescita 2024 (%)": round(c24, 2),
                "Crescita 2025 (%)": round(c25, 2),
                "Prevista 2026 (%)": round(upside_26, 2),
                "Score": score,
                "TradingView": f"https://www.tradingview.com/symbols/{clean_sym}/"
            })
            
            # Recupero News
            ticker_news = t.news
            if ticker_news:
                n = ticker_news[0]
                news_feed.append({
                    "s": sym, "t": n.get('title'), "p": n.get('publisher'), "u": n.get('link')
                })
        except Exception:
            continue
        finally:
            bar.progress((i + 1) / len(pool))
        
    status.empty()
    
    # Protezione contro DataFrame vuoto (Risolve il tuo KeyError)
    if not results:
        return pd.DataFrame(), []

    df_final = pd.DataFrame(results)
    
    # Calcolo Trend Settore
    sector_trend_map = {s: (sum(v)/len(v)) for s, v in sector_scores.items()}
    
    def format_sector_trend(row):
        avg = sector_trend_map.get(row['Settore'], 50)
        return "🚀 Forte" if avg > 65 else "⚖️ Stabile" if avg > 45 else "⚠️ Debole"
    
    df_final['Trend Settore'] = df_final.apply(format_sector_trend, axis=1)
    
    # Ordinamento finale
    df_final = df_final.sort_values(by="Score", ascending=False).head(30)
    
    return df_final, news_feed

# --- INTERFACCIA UTENTE ---

st.title("🏹 S&P 500 Hunter 2026: Analisi Settori & News")

if st.button('🚀 AVVIA SCANSIONE DINAMICA'):
    df_res, news_res = esegui_analisi()
    
    if df_res.empty:
        st.error("Nessun dato recuperato. Verifica la connessione o riprova tra pochi minuti.")
    else:
        st.session_state.df_hunter = df_res
        st.session_state.news_hunter = news_res

if 'df_hunter' in st.session_state:
    st.subheader("📊 Top 30 Titoli per Sentiment")
    st.dataframe(
        st.session_state.df_hunter.drop(columns=['Score']),
        column_config={
            "TradingView": st.column_config.LinkColumn("Grafico", display_text="Apri TV 📈"),
            "Crescita 2024 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Crescita 2025 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Prevista 2026 (%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
        hide_index=True, use_container_width=True
    )
    
    st.divider()
    
    st.subheader("📰 News Feed Leader di Mercato")
    if st.session_state.news_hunter:
        col1, col2 = st.columns(2)
        for idx, n in enumerate(st.session_state.news_hunter[:14]):
            with (col1 if idx % 2 == 0 else col2):
                st.markdown(f"""
                    <div class="news-card">
                        <small>{n['s']} • {n['p']}</small><br>
                        <a href="{n['u']}" target="_blank" style="text-decoration:none; color:#333; font-weight:bold;">
                            {n['t']}
                        </a>
                    </div>
                """, unsafe_allow_html=True)
