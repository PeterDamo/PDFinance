# src/news.py
import yfinance as yf

def recupera_news_aggiornate(lista_ticker):
    """
    Interroga le API per ottenere le ultime notizie dei titoli filtrati.
    Restituisce una lista di dizionari pronti per la visualizzazione.
    """
    feed_news = []
    
    for ticker in lista_ticker:
        try:
            t = yf.Ticker(ticker)
            raw_news = t.news
            if raw_news:
                # Prendiamo solo la news più recente per ogni titolo della Top 20
                top_news = raw_news[0]
                feed_news.append({
                    "ticker": ticker,
                    "titolo": top_news.get('title', 'Nessun titolo'),
                    "publisher": top_news.get('publisher', 'Fonte sconosciuta'),
                    "link": top_news.get('link', '#'),
                    "data": top_news.get('providerPublishTime', '')
                })
        except Exception:
            continue
            
    return feed_news
