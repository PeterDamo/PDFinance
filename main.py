import streamlit as st
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__)))
from src.logic import analizza_mercato_completo, analizza_top_dividendi
from src.news import recupera_news_aggiornate

def carica_css(file_path):
    if os.path.exists(file_path):
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(page_title="Market Hunter 2026", layout="wide")
carica_css(os.path.join("assets", "style.css"))

# SIDEBAR
with st.sidebar:
    st.header("⚙️ Opzioni")
    if st.button("🔄 Svuota Cache e Aggiorna"):
        st.cache_data.clear()
        st.success("Cache pulita!")

st.title("🏹 Market Sentiment Hunter 2026")

if st.button("🚀 AVVIA ANALISI TOTALE"):
    with st.spinner("Scansione mercati in corso..."):
        st.session_state['risultati_score'] = analizza_mercato_completo()
        st.session_state['risultati_div'] = analizza_top_dividendi()
        
        # News basate sulla prima tabella
        all_top_tickers = st.session_state['risultati_score']['Codice'].tolist()
        st.session_state['news_feed'] = recupera_news_aggiornate(all_top_tickers)

# --- TABELLA 1: BUY SCORE ---
if 'risultati_score' in st.session_state:
    st.header("🎯 Top 30: Miglior Buy Score (Crescita & Sentiment)")
    st.dataframe(
        st.session_state['risultati_score'],
        column_config={
            "TradingView": st.column_config.LinkColumn("Grafico", display_text="📈"),
            "Buy Score": st.column_config.ProgressColumn("Score", format="%d", min_value=0, max_value=100),
            "Dividendo (%)": st.column_config.NumberColumn("Div. (%)", format="%.2f%%"),
            "Previsione 2026 (%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
        hide_index=True, use_container_width=True
    )

    st.divider()

    # --- TABELLA 2: DIVIDENDI & PERFORMANCE ---
    st.header("💰 Top 15: Dividend & Growth (Rendimento + Trend)")
    st.write("Selezione basata su dividendi elevati combinati con performance 2025 positiva.")
    st.dataframe(
        st.session_state['risultati_div'],
        column_config={
            "TradingView": st.column_config.LinkColumn("Grafico", display_text="📈"),
            "Dividendo (%)": st.column_config.NumberColumn("Div. (%)", format="%.2f%%"),
            "Perf. 2025 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Buy Score": st.column_config.NumberColumn("Sentiment Score")
        },
        hide_index=True, use_container_width=True
    )

    st.divider()
    st.subheader("📰 Ultime News")
    if 'news_feed' in st.session_state:
        col1, col2 = st.columns(2)
        for i, n in enumerate(st.session_state['news_feed'][:10]): # Limite a 10 news per pulizia
            with (col1 if i % 2 == 0 else col2):
                st.markdown(f"""
                <div style="padding:15px; border-radius:10px; border:1px solid #eeeeee; margin-bottom:12px; background-color:#ffffff;">
                    <b style="color:#555;">{n['ticker']}</b> | <small style="color:#888;">{n['publisher']}</small><br>
                    <a href="{n['link']}" target="_blank" style="color:#444; text-decoration:none; font-weight:500;">{n['titolo']}</a>
                </div>
                """, unsafe_allow_html=True)
