from transformers import pipeline


classifier = pipeline(
    "sentiment-analysis",
    model = "ProsusAI/finbert",
    tokenizer = "ProsusAI/finbert"
)

def analyze(headlines:list):
       results =  classifier(headlines)
       return results

def get_sentiment_label(finbert_label:str)->str:
    mapping = {
        "positive" : "bullish",
        "negative" : "bearish",
        "neutral"  : "neutral"
    }
    return mapping.get(finbert_label,"neutral")