# main.py
import streamlit as st
from src.logic import analizza_titoli_dinamico

st.set_page_config(page_title="Top 20 Sentiment Hunter", layout="wide")

st.title("🎯 Top 20 Titoli per Sentiment - 2026")
st.write("Analisi dinamica basata su dati real-time dei mercati americani.")

if st.button("🚀 Avvia Scansione Mercato"):
    with st.spinner("Analisi in corso... Potrebbe volerci un minuto."):
        df_top20 = analizza_titoli_dinamico()
        st.session_state['risultati'] = df_top20

if 'risultati' in st.session_state:
    df = st.session_state['risultati']
    
    # Mostriamo la tabella con link e formattazione
    st.dataframe(
        df.drop(columns=['Score']),
        column_config={
            "TradingView": st.column_config.LinkColumn("Analisi Grafica", display_text="Vedi Grafico 📈"),
            "Crescita 2024 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Crescita 2025 (%)": st.column_config.NumberColumn(format="%.2f%%"),
        },
        hide_index=True,
        use_container_width=True
    )
    
    # Funzione di download
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Scarica Report Finale (CSV)",
        data=csv,
        file_name="top_20_sentiment_2026.csv",
        mime="text/csv",
    )
