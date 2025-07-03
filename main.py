from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI()

# CORS for React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PostgreSQL connection
def get_connection():
    return psycopg2.connect(
        dbname="rssfeeds",
        user="rssuser",
        password="rsspass",
        host="localhost",
        port="5432"
    )

# /search API
@app.get("/search")
def search_articles(query: str = Query(..., min_length=2)):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT title, link, summary, published, source, tags, sentiment_score,entities

        FROM articles
        WHERE title ILIKE %s OR summary ILIKE %s
        ORDER BY published DESC
        LIMIT 20;
    """, (f"%{query}%", f"%{query}%"))
    results = cur.fetchall()
    cur.close()
    conn.close()
    return results
