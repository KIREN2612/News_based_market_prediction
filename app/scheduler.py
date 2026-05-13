from dotenv import load_dotenv
import os
import feedparser
from app.database import insert_result
from app.sentiment import analyze, get_sentiment_label
from collections import Counter

load_dotenv()

TICKERS = ["INFY", "RELIANCE", "HDFC", "TCS", "WIPRO"]

RSS_FEEDS = [
    "https://www.moneycontrol.com/rss/latestnews.xml",
    "https://www.moneycontrol.com/rss/marketreports.xml",
    "https://economictimes.indiatimes.com/markets/stocks/rss.cms",
    "https://economictimes.indiatimes.com/markets/rss.cms",
    "https://economictimes.indiatimes.com/industry/rss.cms",
    "https://www.business-standard.com/rss/markets-106.rss",
    "https://www.business-standard.com/rss/finance-103.rss",
    "https://www.livemint.com/rss/markets",
    "https://www.livemint.com/rss/companies",
    "https://www.thehindu.com/business/markets/feeder/default.rss",
    "https://www.thehindu.com/business/Industry/feeder/default.rss",
    "https://feeds.feedburner.com/ndtvprofit-latest",
]

KEYWORDS = {
    "INFY":     ["infosys", "infy", "infosys ltd"],
    "RELIANCE": ["reliance", "ril", "reliance industries", "mukesh ambani"],
    "HDFC":     ["hdfc", "hdfc bank", "hdfcbank"],
    "TCS":      ["tcs", "tata consultancy", "tata consultancy services"],
    "WIPRO":    ["wipro", "wipro ltd"],
}

SOURCE_CREDIBILITY = {
    "Moneycontrol":         0.9,
    "The Economic Times":   0.9,
    "Business Standard":    0.85,
    "Mint":                 0.85,
    "Live Mint":            0.85,
    "Reuters":              0.9,
    "Bloomberg":            0.9,
    "NDTV Profit":          0.8,
    "The Hindu Business":   0.8,
    "BusinessLine":         0.8,
    "The Times of India":   0.75,
    "Yahoo Finance":        0.6,
}

def fetch_headlines(ticker: str):
    articles = []
    terms = KEYWORDS.get(ticker, [ticker.lower()])
    seen = set()

    for feed_url in RSS_FEEDS:
        try:
            feed = feedparser.parse(feed_url)
            source_name = feed.feed.get("title", "Unknown")
            for entry in feed.entries:
                title = entry.get("title", "").strip()
                if not title or title in seen:
                    continue
                if any(term in title.lower() for term in terms):
                    seen.add(title)
                    articles.append({
                        "title": title,
                        "source": {"name": source_name}
                    })
        except Exception as e:
            print(f"RSS error {feed_url}: {e}")
            continue

    print(f"{ticker} — {len(articles)} headlines found")
    return articles[:20]

def run_pipeline():
    for ticker in TICKERS:
        articles = fetch_headlines(ticker)
        if not articles:
            print(f"{ticker} — no headlines, skipping")
            continue

        headlines = [a["title"] for a in articles]
        results = analyze(headlines)

        for article, result in zip(articles, results):
            source_name = article["source"]["name"]
            confidence = result["score"]
            label = get_sentiment_label(result["label"])
            source_score = SOURCE_CREDIBILITY.get(source_name, 0.5)
            weighted_score = source_score * confidence

            insert_result(
                ticker=ticker,
                headline=article["title"],
                source=source_name,
                source_score=source_score,
                sentiment=label,
                confidence=confidence,
                weighted_score=weighted_score
            )
        print(f"Done {ticker} — {len(articles)} headlines processed")