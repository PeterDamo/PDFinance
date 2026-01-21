# main.py
import streamlit as st
from src.logic import calcola_sentiment_dinamico, prepara_download_csv

# Configurazione generale (valida per tutta l'app)
st.set_page_config(page_title="Market Hunter 2026", layout="wide")

st.title("🏹 Market Hunter Pro")

# --- SEZIONE ANALISI (Indipendente) ---
if st.button("Avvia Analisi Dinamica"):
    # Chiamiamo la logica esterna
    df_risultati = calcola_sentiment_dinamico(["AAPL", "TSLA", "NVDA"])
    st.session_state['dati'] = df_risultati
    st.success("Analisi Completata!")

# --- SEZIONE VISUALIZZAZIONE (Indipendente) ---
if 'dati' in st.session_state:
    st.subheader("Top 30 Titoli")
    st.dataframe(st.session_state['dati'], use_container_width=True)

    # --- SEZIONE DOWNLOAD (Modificabile senza toccare l'analisi) ---
    csv_data = prepara_download_csv(st.session_state['dati'])
    st.download_button("📥 Scarica Tabella", data=csv_data, file_name="sentiment.csv")
