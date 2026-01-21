# src/logic.py
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime

def get_live_market_tickers():
    """
    Recupera l'elenco aggiornato dei ticker direttamente da Wikipedia (S&P 500).
    Non ci sono ticker fissi: se un titolo esce dall'indice, l'app lo ignora.
    """
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    try:
        # Recupera la tabella dei componenti dell'indice
        df_sp = pd.read_html(url)[0]
        return df_sp['Symbol'].tolist()
    except Exception as e:
        print(f"Errore nel recupero ticker: {e}")
        return []

def esegui_analisi_sentiment():
    """
    Scansiona il mercato e restituisce i 20 titoli con il sentiment migliore.
    """
    tickers = get_live_market_tickers()
    risultati_raw = []
    
    # Analizziamo un pool significativo (es. i primi 100 per capitalizzazione) 
    # per estrarre i 20 migliori in tempi ragionevoli.
    pool_analisi = tickers[:100] 

    for ticker in pool_analisi:
        try:
            # Sostituzione per simboli come BRK.B -> BRK-B per compatibilità Yahoo
            clean_sym = ticker.replace('.', '-')
            t = yf.Ticker(clean_sym)
            
            # Recupero dati storici (ultimi 2 anni per le percentuali richieste)
            hist = t.history(period="3y")
            if hist.empty or len(hist) < 400: continue
            
            info = t.info
            price = info.get('currentPrice', hist['Close'].iloc[-1])
            target = info.get('targetMeanPrice', price)
            
            # 1. Calcolo Percentuali di Crescita Annuali
            # Crescita 2024
            h24 = hist[hist.index.year == 2024]
            c24 = ((h24['Close'].iloc[-1] / h24['Close'].iloc[0]) - 1) * 100 if not h24.empty else 0
            
            # Crescita 2025
            h25 = hist[hist.index.year == 2025]
            c25 = ((h25['Close'].iloc[-1] / h25['Close'].iloc[0]) - 1) * 100 if not h25.empty else 0
            
            # 2. Definizione Trend di Mercato (Media Mobile 200 giorni)
            sma200 = hist['Close'].rolling(window=200).mean().iloc[-1]
            trend = "🚀 Rialzista" if price > sma200 else "⚖️ Consolidamento"
            
            # 3. Calcolo Score Sentiment Proprietario (0-100)
            score = 0
            # Momentum tecnico (30 punti)
            if price > sma200: score += 30
            # Upside potenziale degli analisti (40 punti se > 15%)
            upside = ((target / price) - 1) * 100
            if upside > 15: score += 40
            # Consenso analisti (30 punti se 'Buy')
            if 'buy' in str(info.get('recommendationKey', '')).lower(): score += 30
            
            risultati_raw.append({
                "Codice": clean_sym,
                "Azienda": info.get('longName', ticker),
                "Settore": info.get('sector', 'N/A'),
                "Crescita 2024 (%)": round(c24, 2),
                "Crescita 2025 (%)": round(c25, 2),
                "Trend di Mercato": trend,
                "Sentiment": "🔥 Eccellente" if score >= 80 else "📈 Positivo" if score >= 50 else "⚖️ Neutro",
                "Score": score,
                "TradingView": f"https://www.tradingview.com/symbols/{clean_sym}/"
            })
        except:
            continue

    # CREAZIONE DATAFRAME DINAMICO
    df_totale = pd.DataFrame(risultati_raw)
    
    # Restituiamo solo i 20 migliori in base allo Score calcolato
    if not df_totale.empty:
        return df_totale.sort_values(by="Score", ascending=False).head(20)
    else:
        return pd.DataFrame()
