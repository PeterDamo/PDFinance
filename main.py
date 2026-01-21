#!/usr/bin/env python3
"""
app.py

Analyze market sentiment for S&P500 and Nasdaq and list best N shares based on sentiment + growth.
Outputs top results to console and saves results to top_stocks.csv

Usage:
    python app.py --index both --top 20

Environment variables:
    NEWSAPI_KEY    (optional) key for NewsAPI.org
    FINNHUB_KEY    (optional) key for Finnhub.io (used if NEWSAPI_KEY missing)
"""
import os
import argparse
import time
import math
import concurrent.futures
from datetime import datetime, timedelta
import requests
import pandas as pd
import yfinance as yf
from tqdm import tqdm
import nltk

# Sentiment
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# ensure vader lexicon is downloaded
nltk.download('vader_lexicon', quiet=True)

# Configuration
NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

MAX_CONCURRENT = 8  # concurrency for network calls
NEWS_PER_COMPANY = 6  # number of recent articles to fetch per company
TOP_N_DEFAULT = 20

si = SentimentIntensityAnalyzer()


def get_sp500_tickers():
    """Scrape S&P 500 tickers from Wikipedia"""
    url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
    tables = pd.read_html(url)
    # first table usually contains constituents
    df = tables[0]
    df = df.rename(columns={df.columns[0]: "Symbol"})
    tickers = df['Symbol'].astype(str).tolist()
    companies = df['Security'].astype(str).tolist() if 'Security' in df.columns else [None] * len(tickers)
    return list(zip(tickers, companies))


def get_nasdaq100_tickers():
    """Scrape Nasdaq-100 tickers from Wikipedia"""
    url = "https://en.wikipedia.org/wiki/Nasdaq-100"
    tables = pd.read_html(url)
    # Find table containing 'Ticker' or 'Symbol'
    for t in tables:
        cols = [c.lower() for c in t.columns.astype(str)]
        if any('ticker' in c or 'symbol' in c for c in cols):
            # attempt to standardize
            if 'Ticker' in t.columns:
                tick_col = 'Ticker'
            elif 'Symbol' in t.columns:
                tick_col = 'Symbol'
            else:
                tick_col = t.columns[[i for i,c in enumerate(cols) if 'ticker' in c or 'symbol' in c][0]]
            name_col = None
            for candidate in ['Company', 'Name', 'Company Name', 'Organisation']:
                if candidate in t.columns:
                    name_col = candidate
                    break
            tickers = t[tick_col].astype(str).tolist()
            companies = t[name_col].astype(str).tolist() if name_col else [None]*len(tickers)
            return list(zip(tickers, companies))
    # Fallback
    return []


def fetch_price_metrics(ticker):
    """Return dict with ticker, ytd_growth_pct, two_year_growth_pct, latest_close"""
    now = datetime.utcnow().date()
    two_years_ago = now - timedelta(days=365*2 + 10)
    start_of_year = datetime(now.year, 1, 1).date()

    try:
        t = yf.Ticker(ticker)
        hist = t.history(start=two_years_ago.isoformat(), end=now.isoformat(), interval="1d", auto_adjust=True)
        if hist.empty:
            return {"ticker": ticker, "ytd_growth_pct": None, "two_year_growth_pct": None, "latest_close": None}
        latest_close = hist['Close'].iloc[-1]
        # two-year growth
        first_close = hist['Close'].iloc[0]
        two_year_growth = (latest_close / first_close - 1) * 100 if first_close and not math.isnan(first_close) else None
        # YTD: find first close on/after Jan 1
        ytd_slice = hist.loc[hist.index.date >= start_of_year]
        if not ytd_slice.empty:
            ytd_first = ytd_slice['Close'].iloc[0]
            ytd_growth = (latest_close / ytd_first - 1) * 100 if ytd_first and not math.isnan(ytd_first) else None
        else:
            ytd_growth = None
        return {"ticker": ticker, "ytd_growth_pct": ytd_growth, "two_year_growth_pct": two_year_growth, "latest_close": latest_close}
    except Exception as e:
        return {"ticker": ticker, "ytd_growth_pct": None, "two_year_growth_pct": None, "latest_close": None, "error": str(e)}


def newsapi_fetch(company, ticker, page_size=NEWS_PER_COMPANY):
    """Fetch news via NewsAPI (requires NEWSAPI_KEY)"""
    if not NEWSAPI_KEY:
        return []
    url = "https://newsapi.org/v2/everything"
    q = f"{company} OR {ticker}"
    params = {
        "q": q,
        "apiKey": NEWSAPI_KEY,
        "language": "en",
        "pageSize": page_size,
        "sortBy": "publishedAt"
    }
    try:
        r = requests.get(url, params=params, timeout=20)
        r.raise_for_status()
        j = r.json()
        articles = j.get("articles", [])
        # convert to list of dicts with title, description, url, publishedAt
        out = []
        for a in articles:
            out.append({
                "title": a.get("title"),
                "description": a.get("description"),
                "url": a.get("url"),
                "publishedAt": a.get("publishedAt")
            })
        return out
    except Exception:
        return []


def finnhub_fetch(company, ticker, count=NEWS_PER_COMPANY):
    """Fetch company news via Finnhub (requires FINNHUB_KEY). Tries company name then ticker."""
    if not FINNHUB_KEY:
        return []
    base = "https://finnhub.io/api/v1/company-news"
    to = datetime.utcnow().date()
    frm = to - timedelta(days=7)  # last week
    params = {"symbol": ticker, "from": frm.isoformat(), "to": to.isoformat(), "token": FINNHUB_KEY}
    try:
        r = requests.get(base, params=params, timeout=15)
        r.raise_for_status()
        j = r.json()
        out = []
        for a in j[:count]:
            out.append({
                "title": a.get("headline"),
                "description": a.get("summary"),
                "url": a.get("url"),
                "publishedAt": a.get("datetime")
            })
        return out
    except Exception:
        # fallback to company query via general news endpoints (not provided here)
        return []


def fetch_news(company, ticker):
    # Try NewsAPI first, then Finnhub
    articles = []
    if NEWSAPI_KEY:
        articles = newsapi_fetch(company or "", ticker)
    if not articles and FINNHUB_KEY:
        articles = finnhub_fetch(company or "", ticker)
    return articles


def sentiment_for_articles(articles):
    """Compute average compound sentiment score across articles (title + description)."""
    if not articles:
        return None
    scores = []
    for a in articles:
        text_parts = []
        if a.get("title"):
            text_parts.append(a["title"])
        if a.get("description"):
            text_parts.append(a["description"])
        text = " . ".join(text_parts).strip()
        if not text:
            continue
        s = si.polarity_scores(text)
        scores.append(s['compound'])
    if not scores:
        return None
    return sum(scores) / len(scores)


def analyze_ticker(entry):
    """entry is (ticker, company_name)"""
    ticker, company = entry
    # Normalize ticker for yfinance: some tickers on wiki contain dots or BRK.B style - yfinance handles most
    metrics = fetch_price_metrics(ticker)
    articles = fetch_news(company, ticker)
    sentiment = sentiment_for_articles(articles)
    return {
        "ticker": ticker,
        "company": company,
        "ytd_growth_pct": metrics.get("ytd_growth_pct"),
        "two_year_growth_pct": metrics.get("two_year_growth_pct"),
        "latest_close": metrics.get("latest_close"),
        "sentiment": sentiment,
        "news": articles
    }


def compute_score(row, ytd_min, ytd_max):
    """Combine sentiment and normalized YTD growth into a single score."""
    s = row.get("sentiment")
    g = row.get("ytd_growth_pct")
    # Normalize g to [0,1] between ytd_min and ytd_max if possible
    if g is None or ytd_min is None or ytd_max is None or ytd_min == ytd_max:
        g_norm = 0.0
    else:
        g_norm = (g - ytd_min) / (ytd_max - ytd_min)
        g_norm = max(0.0, min(1.0, g_norm))
    # sentiment is in [-1,1] -> normalize to [0,1]
    if s is None:
        s_norm = 0.5  # neutral default
    else:
        s_norm = (s + 1) / 2
    # Weighted sum: sentiment 60%, growth 40% (tunable)
    score = 0.6 * s_norm + 0.4 * g_norm
    return score


def main(args):
    entries = []
    if args.index in ("sp500", "both"):
        entries.extend(get_sp500_tickers())
    if args.index in ("nasdaq", "both"):
        entries.extend(get_nasdaq100_tickers())

    if args.limit:
        entries = entries[:args.limit]

    print(f"Analyzing {len(entries)} tickers (this may take a while; be mindful of API rate limits)...")

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_CONCURRENT) as exe:
        futures = [exe.submit(analyze_ticker, e) for e in entries]
        for f in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            try:
                r = f.result()
                results.append(r)
            except Exception as e:
                # keep going
                pass

    df = pd.DataFrame(results)

    # Prepare numeric columns
    ytd_vals = df['ytd_growth_pct'].dropna().astype(float)
    ytd_min = float(ytd_vals.min()) if not ytd_vals.empty else None
    ytd_max = float(ytd_vals.max()) if not ytd_vals.empty else None

    df['score'] = df.apply(lambda r: compute_score(r, ytd_min, ytd_max), axis=1)

    # sort by score and then by sentiment and ytd growth as tie-breakers
    df_sorted = df.sort_values(by=['score', 'sentiment', 'ytd_growth_pct'], ascending=[False, False, False])

    top_n = args.top or TOP_N_DEFAULT
    top_df = df_sorted.head(top_n)

    # Present results
    out_rows = []
    now_tag = datetime.utcnow().isoformat()
    for _, row in top_df.iterrows():
        news_items = row.get("news") or []
        news_brief = []
        for n in (news_items[:3]):
            title = n.get("title") or ""
            url = n.get("url") or ""
            news_brief.append(f"{title} ({url})")
        out_rows.append({
            "ticker": row.get("ticker"),
            "company": row.get("company"),
            "score": round(float(row.get("score") or 0), 4),
            "sentiment": None if row.get("sentiment") is None else round(float(row.get("sentiment")), 4),
            "ytd_growth_pct": None if row.get("ytd_growth_pct") is None else round(float(row.get("ytd_growth_pct")), 2),
            "two_year_growth_pct": None if row.get("two_year_growth_pct") is None else round(float(row.get("two_year_growth_pct")), 2),
            "latest_close": None if row.get("latest_close") is None else round(float(row.get("latest_close")), 4),
            "top_news": " | ".join(news_brief)
        })

    out_df = pd.DataFrame(out_rows)
    out_csv = args.output or "top_stocks.csv"
    out_df.to_csv(out_csv, index=False)
    print(f"\nTop {top_n} stocks saved to {out_csv}\n")
    print(out_df.to_string(index=False))

    return out_df


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rank stocks by sentiment and growth")
    parser.add_argument("--index", choices=["sp500", "nasdaq", "both"], default="both", help="which index to analyze")
    parser.add_argument("--top", type=int, default=20, help="how many top stocks to return")
    parser.add_argument("--limit", type=int, default=0, help="limit number of tickers (for testing)")
    parser.add_argument("--output", type=str, default="top_stocks.csv", help="output CSV filename")
    args = parser.parse_args()
    if args.limit and args.limit > 0:
        args.limit = int(args.limit)
    else:
        args.limit = None
    main(args)
