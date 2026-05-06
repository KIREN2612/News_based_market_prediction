from fastapi import FastAPI
from pydantic import BaseModel
from app.database import create_table,get_latest_by_ticker
from app.cache import set_cache,get_cache
from contextlib import asynccontextmanager
from app.scheduler import run_pipeline
from apscheduler.schedulers.background import BackgroundScheduler

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

class main(BaseModel):
    ticker :  str
    price  :  float
    
@app.get("/health")
def health_check():
    return{"Status 200" : "OK"}

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
    
    result = {"ticker":ticker,"rows":rows}
    set_cache(ticker,result)
    
    return{"source":"database","data":result}