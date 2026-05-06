import sqlite3
from datetime import datetime

DB_PATH = "sentiment.db"

def get_connection():
    sqliteConnection = sqlite3.connect(DB_PATH)
    return sqliteConnection

def create_table():
    sqliteConnection = sqlite3.connect(DB_PATH)
    cursor = sqliteConnection.cursor()  
    
    table_creation_query = """CREATE TABLE IF NOT EXISTS sentiment_results(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticker text,
        headline text,
        source text,
        source_score real,
        sentiment text,
        confidence real,
        weighted_score real,
        fetched_at DATETIME
        );
        """
    cursor.execute(table_creation_query)
    sqliteConnection.commit()
    print("Table has been created")
    cursor.close()
    
def insert_result(ticker, headline, source, source_score, sentiment, confidence, weighted_score):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO sentiment_results 
        (ticker, headline, source, source_score, sentiment, confidence, weighted_score, fetched_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (ticker, headline, source, source_score, sentiment, confidence, weighted_score, datetime.now()))

    conn.commit()
    conn.close()
    
def get_latest_by_ticker(ticker: str):
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT * FROM sentiment_results
        WHERE ticker = ?
        ORDER BY fetched_at DESC
        LIMIT 10
    """, (ticker,))
    
    rows = cursor.fetchall()
    conn.close()
    return rows

