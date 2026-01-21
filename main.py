# main.py
import streamlit as st
import sys
import os

sys.path.append(os.path.dirname(__file__))
from src.logic import analizza_titoli_dinamico

def carica_css(file_path):
    with open(file_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.set_page_config(page_title="Market Hunter 2026", layout="wide")

# Caricamento CSS Assets
css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    carica_css(css_path)

st.title("🏹 Market Sentiment Hunter 2026")
st.write("Analisi quantitativa dei 500 titoli S&P 500 con Score predittivo.")

if st.button("🚀 Avvia Scansione Completa"):
    with st.spinner("Analisi profonda dei 500 titoli in corso..."):
        df = analizza_titoli_dinamico()
        
        if df is not None and not df.empty:
            st.session_state['risultati'] = df
        else:
            st.warning("Non ci sono titoli analizzati")

if 'risultati' in st.session_state:
    st.subheader("I 20 migliori titoli consigliati")
    
    # Visualizzazione Tabella
    st.dataframe(
        st.session_state['risultati'],
        column_config={
            "TradingView": st.column_config.LinkColumn("Grafico", display_text="Vedi 📈"),
            "Buy Score": st.column_config.ProgressColumn(
                "Buy Score",
                help="Punteggio da 0 a 100 basato su Trend, Target e Consenso",
                format="%d",
                min_value=0,
                max_value=100,
            ),
            "Andamento 2024 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Andamento 2025 (%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
        hide_index=True,
        use_container_width=True
    )
    
    st.download_button(
        "📥 Scarica Report Completo CSV", 
        data=st.session_state['risultati'].to_csv(index=False).encode('utf-8'), 
        file_name="market_analysis_2026.csv"
    )
