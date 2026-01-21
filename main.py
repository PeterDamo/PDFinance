# main.py
import streamlit as st
import sys
import os

# Path setup per cartella src
sys.path.append(os.path.dirname(__file__))
from src.logic import analizza_titoli_dinamico

def carica_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(page_title="Market Hunter Pro", layout="wide")

# Caricamento CSS (Asset grigio/bianco)
css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    carica_css(css_path)

st.title("🏹 Market Sentiment Hunter 2026")
st.write("Analisi completa dei 500 titoli S&P 500 in tempo reale.")

if st.button("🚀 Avvia Scansione Completa"):
    with st.spinner("Scansione dei 500 titoli in corso... Attendere."):
        df = analizza_titoli_dinamico()
        
        if df is not None and not df.empty:
            st.session_state['risultati'] = df
        else:
            # Messaggio richiesto se l'analisi fallisce o non trova nulla
            st.warning("Non ci sono titoli analizzati")

if 'risultati' in st.session_state:
    st.subheader("I 20 migliori titoli per Sentiment")
    st.dataframe(
        st.session_state['risultati'].drop(columns=['Score']),
        column_config={
            "TradingView": st.column_config.LinkColumn("Grafico", display_text="Vedi 📈")
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Download button
    csv = st.session_state['risultati'].to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Tabella CSV", data=csv, file_name="analisi_mercato.csv")
