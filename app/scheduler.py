from dotenv import load_dotenv
import os
import requests
from app.database import insert_result
from app.sentiment import analyze,get_sentiment_label


load_dotenv()

NEWS_API_KEY = os.getenv("NEWS_API_KEY")

tickers = ["INFY", "RELIANCE", "HDFC", "TCS", "WIPRO"]

def fetch_headlines(ticker: str):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": ticker,
        "language": "en",
        "pageSize": 10,
        "apiKey": NEWS_API_KEY
    }
    response = requests.get(url, params=params)
    data = response.json()
    
    if data.get("status") != "ok":
        print(f"NewsAPI error for {ticker}: {data.get('message', 'unknown error')}")
        return []
    
    return data.get("articles", [])

SOURCE_CREDIBILITY = {
    "Moneycontrol": 0.9,
    "The Economic Times": 0.9,
    "Business Standard": 0.85,
    "Mint": 0.85,
    "Reuters": 0.9,
    "Bloomberg": 0.9,
    "NDTV Profit": 0.8,
    "LiveMint": 0.85,
    "BusinessLine": 0.8,
    "The Times of India": 0.75,
    "MarketBeat": 0.7,
    "Yahoo Entertainment": 0.5,
}

def run_pipeline():
    for ticker in tickers:
        articles = fetch_headlines(ticker)
        
        if not articles:
            continue
        
        headlines = [a["title"]for a in articles if a["title"]]
        
        results = analyze(headlines)
        
        for article,result in zip(articles,results):
            source_name = article["source"]["name"]
            confidence = result["score"]
            label = get_sentiment_label(result["label"])
            
            source_score = SOURCE_CREDIBILITY.get(source_name,0.4)
            weighted_score = source_score * confidence
            
            insert_result(
                ticker = ticker,
                headline = article["title"],
                source = source_name,
                source_score = source_score,
                sentiment = label,
                confidence= confidence,
                weighted_score = weighted_score
            )
        print(f"Done{ticker} - {len(articles)} headlines processed")
        

