# main.py
import streamlit as st
import sys
import os

# Assicurati che src sia visibile
sys.path.append(os.path.dirname(__file__))

from src.logic import analizza_titoli_dinamico

st.set_page_config(page_title="Market Hunter", layout="wide")

st.title("🏹 Market Sentiment Hunter 2026")

if st.button("🚀 Avvia Analisi Dinamica"):
    with st.spinner("Scansione mercati in corso..."):
        df = analizza_titoli_dinamico()
        if not df.empty:
            st.session_state['risultati'] = df
        else:
            st.error("Errore nel recupero dati. Riprova tra un istante.")

if 'risultati' in st.session_state:
    st.dataframe(
        st.session_state['risultati'].drop(columns=['Score']),
        column_config={
            "TradingView": st.column_config.LinkColumn("Grafico", display_text="Vedi 📈")
        },
        hide_index=True,
        use_container_width=True
    )
