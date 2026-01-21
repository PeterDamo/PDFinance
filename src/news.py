# src/news.py
import yfinance as yf

def recupera_news_aggiornate(lista_ticker):
    feed_news = []
    for ticker in lista_ticker:
        try:
            t = yf.Ticker(ticker)
            raw_news = t.news
            if raw_news:
                top_news = raw_news[0]
                feed_news.append({
                    "ticker": ticker,
                    "titolo": top_news.get('title', 'Nessun titolo'),
                    "publisher": top_news.get('publisher', 'Fonte sconosciuta'),
                    "link": top_news.get('link', '#')
                })
        except: continue
    return feed_news
