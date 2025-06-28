import feedparser
import psycopg2
from datetime import datetime
from urllib.parse import urlparse
url = ["https://bfsi.economictimes.indiatimes.com/rss/lateststories","https://timesofindia.indiatimes.com/rssfeeds/1898055.cmshttps://timesofindia.indiatimes.com/rssfeeds/1898055.cms"]

for i in url:
    feed = feedparser.parse(i)

    # Connect to Postgres
    conn = psycopg2.connect(
        dbname="rssfeeds",
        user="rssuser",
        password="rsspass",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()
    
    parsed = urlparse(i)
    source = f"{parsed.hostname}"
    for entry in feed.entries:
        title = entry.title
        link = entry.link
        summary = entry.description if 'summary' in entry else ''
        published = datetime(*entry.published_parsed[:6]) if 'published_parsed' in entry else None
        # source = "*"

        try:
            cur.execute("""
                INSERT INTO articles (title, link, summary, published, source)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (link) DO NOTHING;
            """, (title, link, summary, published, source))
        except Exception as e:
            print(f"Error inserting {title[:30]}...: {e}")

conn.commit()
cur.close()
conn.close()
print("Feed parsed and stored.")