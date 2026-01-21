import streamlit as st
import sys
import os
import pandas as pd

# Path setup per individuare correttamente la cartella 'src'
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.logic import analizza_mercato_completo
from src.news import recupera_news_aggiornate

def carica_css(file_path):
    if os.path.exists(file_path):
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(page_title="Market Hunter 2026", layout="wide")
carica_css(os.path.join("assets", "style.css"))

st.title("🏹 Market Sentiment Hunter 2026")
st.write("Analisi S&P 500, NASDAQ-100 ed ETF con Score di acquisto.")

if st.button("🚀 AVVIA SCANSIONE COMPLETA (TOP 30)"):
    with st.spinner("Scansione di oltre 600 asset in corso..."):
        df = analizza_mercato_completo()
        
        if df is not None and not df.empty:
            st.session_state['risultati'] = df
            st.session_state['news_feed'] = recupera_news_aggiornate(df['Codice'].tolist())
        else:
            st.warning("Non ci sono titoli analizzati")

if 'risultati' in st.session_state:
    st.divider()
    st.subheader("📊 Top 30 Opportunità di Mercato")
    
    st.dataframe(
        st.session_state['risultati'],
        column_config={
            "TradingView": st.column_config.LinkColumn("Grafico", display_text="Vedi 📈"),
            "Buy Score": st.column_config.ProgressColumn("Score", format="%d", min_value=0, max_value=100),
            "Dividendo (%)": st.column_config.NumberColumn(
                "Div. (%)", 
                format="%.2f%%", # Moltiplica per 100 il decimale e mostra il %
                help="Rendimento annuo atteso dai dividendi"
            ),
            "Perf. 2024 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Perf. 2025 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Previsione 2026 (%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
        hide_index=True,
        use_container_width=True
    )

    # Download CSV
    csv = st.session_state['risultati'].to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Report CSV", data=csv, file_name="market_hunter_2026.csv")

    st.divider()
    st.subheader("📰 Ultime News: Sentiment Correlato")
    if 'news_feed' in st.session_state:
        col1, col2 = st.columns(2)
        for i, n in enumerate(st.session_state['news_feed']):
            target_col = col1 if i % 2 == 0 else col2
            with target_col:
                st.markdown(f"""
                <div style="padding:15px; border-radius:10px; border:1px solid #eeeeee; margin-bottom:12px; background-color:#ffffff;">
                    <b style="color:#555;">{n['ticker']}</b> | <small style="color:#888;">{n['publisher']}</small><br>
                    <a href="{n['link']}" target="_blank" style="color:#444; text-decoration:none; font-weight:500;">{n['titolo']}</a>
                </div>
                """, unsafe_allow_html=True)
