# main.py
import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(__file__))
from src.logic import analizza_titoli_dinamico
from src.news import recupera_news_aggiornate

def carica_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(page_title="Market Hunter 2026", layout="wide")

css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    carica_css(css_path)

st.title("🏹 Market Sentiment Hunter 2026")

if st.button("🚀 Avvia Scansione Completa"):
    with st.spinner("Analisi profonda dei 500 titoli e recupero news..."):
        df = analizza_titoli_dinamico()
        if not df.empty:
            st.session_state['risultati'] = df
            st.session_state['news_feed'] = recupera_news_aggiornate(df['Codice'].tolist())
        else:
            st.warning("Non ci sono titoli analizzati")

if 'risultati' in st.session_state:
    st.subheader("📊 Classifica Top 20: Dati e Rendimenti")
    
    st.dataframe(
        st.session_state['risultati'],
        column_config={
            "TradingView": st.column_config.LinkColumn("Grafico", display_text="Vedi 📈"),
            "Buy Score": st.column_config.ProgressColumn("Score", format="%d", min_value=0, max_value=100),
            "Dividendo (%)": st.column_config.NumberColumn(format="%.2f%%"), # Formattazione Dividendo
            "Andamento 2024 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Andamento 2025 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Previsione 2026 (%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
        hide_index=True,
        use_container_width=True
    )

    st.divider()

    st.subheader("📰 Ultime News: Sentiment Correlato")
    if 'news_feed' in st.session_state:
        col1, col2 = st.columns(2)
        for i, n in enumerate(st.session_state['news_feed']):
            target_col = col1 if i % 2 == 0 else col2
            with target_col:
                st.markdown(f"""
                <div style="padding:12px; border-radius:8px; border:1px solid #eeeeee; margin-bottom:10px; background-color:#ffffff;">
                    <b style="color:#555;">{n['ticker']}</b> | <small style="color:#888;">{n['publisher']}</small><br>
                    <a href="{n['link']}" target="_blank" style="color:#444; text-decoration:none; font-size:14px;">{n['titolo']}</a>
                </div>
                """, unsafe_allow_html=True)
