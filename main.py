import streamlit as st
import sys
import os

# Aggiunge la cartella 'src' al path per caricare i moduli logici
sys.path.append(os.path.join(os.path.dirname(__file__)))

from src.logic import analizza_mercato_completo, analizza_top_dividendi
from src.news import recupera_news_aggiornate

def carica_css(file_path):
    """Carica il tema bianco/grigio personalizzato."""
    if os.path.exists(file_path):
        with open(file_path) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# Configurazione della Pagina
st.set_page_config(
    page_title="Market Hunter 2026",
    page_icon="🏹",
    layout="wide"
)

# Caricamento Asset Grafici
carica_css(os.path.join("assets", "style.css"))

# --- SIDEBAR: GESTIONE CACHE ---
with st.sidebar:
    st.header("⚙️ Impostazioni")
    st.write("I dati vengono aggiornati ogni ora per garantire velocità e precisione.")
    if st.button("🔄 Svuota Cache e Riavvia"):
        st.cache_data.clear()
        st.success("Cache pulita! Riavvia l'analisi.")

# --- INTESTAZIONE ---
st.title("🏹 Market Sentiment Hunter 2026")
st.markdown("""
    Scansione avanzata di **S&P 500**, **NASDAQ-100** ed **ETF Leader**. 
    Identifichiamo le migliori opportunità incrociando dati storici, previsioni degli analisti e rendimenti da dividendo.
""")

# --- AZIONE PRINCIPALE ---
if st.button("🚀 AVVIA ANALISI TOTALE MERCATO"):
    with st.spinner("Scansione di oltre 600 asset e calcolo sentiment..."):
        # Recupero dati dal motore logico (con cache attiva)
        st.session_state['risultati_score'] = analizza_mercato_completo()
        st.session_state['risultati_div'] = analizza_top_dividendi()
        
        # Recupero news per i titoli in evidenza
        top_tickers = st.session_state['risultati_score']['Codice'].head(10).tolist()
        st.session_state['news_feed'] = recupera_news_aggiornate(top_tickers)

# --- VISUALIZZAZIONE RISULTATI ---
if 'risultati_score' in st.session_state:
    
    # --- TABELLA 1: GROWTH & SENTIMENT ---
    st.header("🎯 Top 30: Crescita & Sentiment (Buy Score)")
    st.write("I titoli con il miglior momentum tecnico e consenso degli analisti per il 2026.")
    
    st.dataframe(
        st.session_state['risultati_score'],
        column_config={
            "TradingView": st.column_config.LinkColumn("Link", display_text="📈"),
            "Buy Score": st.column_config.ProgressColumn("Score", format="%d", min_value=0, max_value=100),
            "Dividendo (%)": st.column_config.NumberColumn("Div. (%)", format="%.2f%%"),
            "Perf. 2024 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Perf. 2025 (%)": st.column_config.NumberColumn(format="%.2f%%"),
            "Previsione 2026 (%)": st.column_config.NumberColumn("Target 2026", format="%.2f%%"),
        },
        hide_index=True,
        use_container_width=True
    )

    st.divider()

    # --- TABELLA 2: DIVIDEND & GROWTH ---
    st.header("💰 Top 15: Dividend & Performance")
    st.write("Aziende solide con dividendi elevati e trend di crescita confermato nell'ultimo anno.")
    
    st.dataframe(
        st.session_state['risultati_div'],
        column_config={
            "TradingView": st.column_config.LinkColumn("Link", display_text="📈"),
            "Dividendo (%)": st.column_config.NumberColumn("Resa Annua", format="%.2f%%"),
            "Perf. 2025 (%)": st.column_config.NumberColumn("Crescita 2025", format="%.2f%%"),
            "Buy Score": st.column_config.NumberColumn("Sentiment Score", format="%d")
        },
        hide_index=True,
        use_container_width=True
    )

    st.divider()

    # --- SEZIONE NEWS ---
    st.subheader("📰 Ultime News: Focus sui Leader di Mercato")
    if 'news_feed' in st.session_state and st.session_state['news_feed']:
        col1, col2 = st.columns(2)
        for i, n in enumerate(st.session_state['news_feed']):
            target_col = col1 if i % 2 == 0 else col2
            with target_col:
                st.markdown(f"""
                <div style="padding:15px; border-radius:10px; border:1px solid #eeeeee; margin-bottom:12px; background-color:#ffffff; border-left: 5px solid #cccccc;">
                    <b style="color:#555;">{n['ticker']}</b> | <small style="color:#888;">{n['publisher']}</small><br>
                    <a href="{n['link']}" target="_blank" style="color:#222; text-decoration:none; font-weight:500; font-size:15px;">{n['titolo']}</a>
                </div>
                """, unsafe_allow_html=True)
    
    # Download Report Generale
    csv = st.session_state['risultati_score'].to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Scarica Analisi Completa (CSV)",
        data=csv,
        file_name="market_hunter_2026_report.csv",
        mime="text/csv",
    )

else:
    st.info("👋 Benvenuto! Clicca sul pulsante 'Avvia Analisi' per scansionare il mercato in tempo reale.")
