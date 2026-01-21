
# Importazione dei moduli personalizzati
try:import streamlit as st
import sys
import os
import pandas as pd

# Forza l'aggiunta della cartella 'src' al path di sistema per evitare errori di importazione
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

    from src.logic import analizza_mercato_completo
    from src.news import recupera_news_aggiornate
except ImportError:
    st.error("Errore: Assicurati che i file 'logic.py' e 'news.py' siano nella cartella 'src'.")

# --- FUNZIONI DI SUPPORTO ---
def carica_css(file_path):
    """Carica il file CSS esterno per definire il tema Bianco/Grigio."""
    if os.path.exists(file_path):
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(
    page_title="Market Hunter 2026 | Analisi Dinamica",
    page_icon="🎯",
    layout="wide"
)

# Applichiamo il CSS (Assets)
carica_css(os.path.join("assets", "style.css"))

# --- INTERFACCIA UTENTE ---
st.title("🏹 Market Sentiment Hunter 2026")
st.markdown("""
    Analisi dinamica in tempo reale di **S&P 500**, **NASDAQ-100** e **ETF Leader**. 
    Il sistema scansiona i mercati, calcola i trend storici e il sentiment futuro per identificare i 30 migliori asset.
""")

# Pulsante di Scansione
if st.button("🚀 AVVIA SCANSIONE COMPLETA (AZIONI + ETF)"):
    with st.spinner("Scansione di oltre 600 strumenti finanziari in corso..."):
        # Esecuzione del motore di analisi (ritorna i 30 migliori)
        df_risultati = analizza_mercato_completo()
        
        if df_risultati is not None and not df_risultati.empty:
            st.session_state['risultati'] = df_risultati
            
            # Recupero news correlate solo per i 30 ticker identificati
            tickers_identificati = df_risultati['Codice'].tolist()
            st.session_state['news_feed'] = recupera_news_aggiornate(tickers_identificati)
            st.success("Analisi completata con successo!")
        else:
            st.warning("Non ci sono titoli analizzati. Verifica la connessione API.")

# --- VISUALIZZAZIONE DATI ---
if 'risultati' in st.session_state:
    st.divider()
    st.subheader("📊 Top 30 Opportunità: Classifica per Buy Score")
    
    # Visualizzazione Tabella Pro
st.dataframe(
        st.session_state['risultati'],
        column_config={
            "TradingView": st.column_config.LinkColumn("Grafico", display_text="Vedi 📈"),
            "Buy Score": st.column_config.ProgressColumn(
                "Buy Score",
                format="%d",
                min_value=0,
                max_value=100,
            ),
            # FORMATTAZIONE FORZATA: il suffisso % viene aggiunto visivamente
            "Dividendo (%)": st.column_config.NumberColumn(
                "Dividendo (%)",
                format="%.2f%%", # Questo aggiunge il simbolo % alla fine del numero
                help="Rendimento da dividendo annuo calcolato in percentuale"
            ),
            "Perf. 2024 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Perf. 2025 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Previsione 2026 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Tipo": st.column_config.TextColumn("Tipo")
        },
        hide_index=True,
        use_container_width=True
    )


    # Download Report
    csv = st.session_state['risultati'].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Scarica Report Analisi (CSV)",
        data=csv,
        file_name="market_hunter_analysis.csv",
        mime="text/csv",
    )

    st.divider()

    # --- SEZIONE NEWS ---
    st.subheader("📰 Sentiment News: Ultime dagli Analisti")
    
    if 'news_feed' in st.session_state and st.session_state['news_feed']:
        # Layout a due colonne per le notizie
        col1, col2 = st.columns(2)
        for i, news in enumerate(st.session_state['news_feed']):
            target_col = col1 if i % 2 == 0 else col2
            with target_col:
                st.markdown(f"""
                    <div style="padding:15px; border-radius:10px; border:1px solid #eeeeee; margin-bottom:12px; background-color:#ffffff;">
                        <span style="color:#888; font-size:12px; font-weight:bold;">{news['ticker']} • {news['publisher']}</span><br>
                        <a href="{news['link']}" target="_blank" style="color:#333; text-decoration:none; font-weight:500; font-size:15px;">
                            {news['titolo']}
                        </a>
                    </div>
                """, unsafe_allow_html=True)
    else:
        st.info("Nessuna news recente disponibile per i titoli in classifica.")

else:
    # Stato iniziale dell'app
    st.info("Clicca sul pulsante sopra per iniziare l'analisi dei mercati.")
