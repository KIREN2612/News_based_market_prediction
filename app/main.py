from fastapi import FastAPI
from pydantic import BaseModel
from app.database import create_table,get_latest_by_ticker
from app.cache import set_cache,get_cache
from contextlib import asynccontextmanager
from app.scheduler import run_pipeline
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_table()
    print("Database setup successfully")
    
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_pipeline,"interval",minutes=3)
    scheduler.start()
    print("Scheduler started")
    
    yield
    
    scheduler.shutdown()
    print("Scheduler shutdown")

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve_dashboard():
    return FileResponse("frontend/index.html")

#--------Helper Aggreggator function------------------
from collections import Counter

def aggregate_sentiment(ticker:str,rows:list):
    scores = [row["weighted_score"]for row in rows]
    labels = [row["sentiment"]for row in rows]
    
    conviction = sum(scores)/len(scores)
    
    signal = Counter(labels).most_common(1)[0][0]
    
    freshness = rows[0]["fetched_at"]
    
    return{
        "ticker":ticker,
        "signal":signal,
        "conviction": round(conviction,2),
        "based_on" : len(rows),
        "freshness" : freshness
    }

class main(BaseModel):
    ticker :  str
    price  :  float
    
@app.get("/health")
def health_check():
    return{"Status 200" : "OK"}

@app.get("/tickers")
def get_all_tickers():
    results = []
    for ticker in ["INFY", "RELIANCE", "HDFC", "TCS", "WIPRO"]:
        cached = get_cache(ticker)
        if cached:
            results.append({"source":"cached","data":cached}) 
            continue
        rows = get_latest_by_ticker(ticker)
        if rows:
            result = aggregate_sentiment(ticker,rows)
            set_cache(ticker,result)
            results.append({"source":"database","data":result})
        else:
            results.append({"ticker":ticker,"message":"No data yet"})
    return results

@app.get("/sentiment/{ticker}")
def ticker_details(ticker:str):
    #check cache #1
    cached = get_cache(ticker)
    if cached:
        return {"source":"cache","data":cached}
    #if cache doesnt have check db:
    rows = get_latest_by_ticker(ticker)
    if not rows:
        return{"ticker":ticker,"message":'No data yet-scheduler has not run yet'}   
    
    result = aggregate_sentiment(ticker, rows)
    set_cache(ticker, result)
    
    return{"source":"database","data":result}