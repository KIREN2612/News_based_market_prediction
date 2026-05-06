from datetime import datetime

cache = {}

cache_TTL = 60

def set_cache(ticker:str,data:dict):
    cache[ticker] = {
        "data":data,
        "time":datetime.now()
    }
def get_cache(ticker:str):
    if ticker not in cache:
        return None
    stored_at = cache[ticker]["time"]
    seconds_elapsed = (datetime.now()-stored_at).total_seconds()
    if seconds_elapsed > cache_TTL:
        return None
    return cache[ticker]["data"]