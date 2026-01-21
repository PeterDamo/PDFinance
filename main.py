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

# Caricamento Stile (Bianco/Grigio)
css_path = os.path.join("assets", "style.css")
if os.path.exists(css_path):
    carica_css(css_path)

st.title("🏹 Market Sentiment Hunter 2026")
st.write("Scansione live S&P 500: Analisi storica e potenziale di crescita 2026.")

if st.button("🚀 Avvia Scansione Completa"):
    with st.spinner("Analisi dei 500 titoli in corso..."):
        df = analizza_titoli_dinamico()
        if not df.empty:
            st.session_state['risultati'] = df
        else:
            st.warning("Non ci sono titoli analizzati")

if 'risultati' in st.session_state:
    st.subheader("Top 20 Titoli per Opportunità")
    
    st.dataframe(
        st.session_state['risultati'],
        column_config={
            "TradingView": st.column_config.LinkColumn("Grafico", display_text="Vedi 📈"),
            "Buy Score": st.column_config.ProgressColumn("Score", format="%d", min_value=0, max_value=100),
            "Andamento 2024 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Andamento 2025 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Previsione 2026 (%)": st.column_config.NumberColumn(
                "Previsione 2026",
                help="Upside potenziale basato sul Target Price medio degli analisti",
                format="%.2f%%"
            ),
        },
        hide_index=True,
        use_container_width=True
    )
    
    csv = st.session_state['risultati'].to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica Report CSV", data=csv, file_name="analisi_2026.csv")
