import feedparser
import psycopg2
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from transformers import pipeline
from newspaper import Article
from sentence_transformers import SentenceTransformer
import spacy
import torch

# Load AI models
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
nlp = spacy.load("en_core_web_sm")

default_summary_padding = ("This article discusses the topic in detail including relevant background, context, and implications. " * 10)

rss_sources = {
    "General News": [
        "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
        "https://www.hindustantimes.com/rss/topnews/rssfeed.xml"
    ]
}

# Connect to database
conn = psycopg2.connect(dbname="rssfeeds", user="rssuser", password="rsspass", host="localhost", port="5432")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    title TEXT,
    link TEXT UNIQUE,
    summary TEXT,
    published TIMESTAMP,
    source TEXT,
    tags TEXT,
    sentiment_score INTEGER,
    entities TEXT
);
""")
conn.commit()

def split_to_chunks(text, max_words=400):
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    chunks, chunk = [], ""
    for sent in sentences:
        if len((chunk + " " + sent).split()) <= max_words:
            chunk += " " + sent
        else:
            chunks.append(chunk.strip())
            chunk = sent
    if chunk:
        chunks.append(chunk.strip())
    return chunks

def extract_dynamic_tags(doc):
    # Use NER and POS to extract dynamic tags (nouns, proper nouns, orgs, etc.)
    tags = set()
    for ent in doc.ents:
        if ent.label_ in {"ORG", "PERSON", "GPE", "EVENT", "PRODUCT", "LAW"}:
            tags.add(ent.text.lower())

    for token in doc:
        if token.pos_ in {"NOUN", "PROPN"} and not token.is_stop and len(token.text) > 2:
            tags.add(token.lemma_.lower())
    return list(tags)

for category, urls in rss_sources.items():
    for url in urls:
        feed = feedparser.parse(url)
        hostname = urlparse(url).hostname or "unknown"

        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")

            raw_summary = entry.get("summary", entry.get("description", ""))
            summary = BeautifulSoup(raw_summary, "html.parser").get_text().strip()

            # Try extracting full article
            try:
                article = Article(link)
                article.download()
                article.parse()
                summary2 = article.text.strip()
            except:
                summary2 = summary

            if not summary2 or len(summary2.split()) < 50:
                continue

            published = datetime(*entry.published_parsed[:6]) if "published_parsed" in entry else None
            source = f"{category} - {hostname}"

            while len(summary2.split()) < 100:
                summary2 += " " + default_summary_padding

            chunks = split_to_chunks(summary2)
            all_tags = set()
            all_entities = set()
            total_score = 0
            count = 0

            for chunk in chunks:
                try:
                    # Sentiment
                    result = sentiment_analyzer(chunk[:512])[0]
                    label, score = result["label"], result["score"]
                    if label == "POSITIVE":
                        sentiment = min(5, max(4, round(score * 5)))
                    elif label == "NEGATIVE":
                        sentiment = max(1, min(2, round((1 - score) * 5)))
                    else:
                        sentiment = 3
                    total_score += sentiment
                    count += 1
                except:
                    continue

                # NER + Tagging
                try:
                    doc = nlp(chunk)
                    all_entities.update([ent.text for ent in doc.ents])
                    tags = extract_dynamic_tags(doc)
                    all_tags.update(tags)
                except:
                    continue

            if not all_tags or count == 0:
                print(f"⏭️ Skipped: {title[:60]} — Missing tags or sentiment")
                continue

            tags = ", ".join(sorted(all_tags))
            entities = ", ".join(sorted(set(all_entities)))
            sentiment_score = round(total_score / count)

            try:
                cur.execute("""
                    INSERT INTO articles (title, link, summary, published, source, tags, sentiment_score, entities)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (link) DO UPDATE SET
                        tags = EXCLUDED.tags,
                        sentiment_score = EXCLUDED.sentiment_score,
                        entities = EXCLUDED.entities;
                """, (title, link, summary2, published, source, tags, sentiment_score, entities))
                print(f"✅ Saved: {title[:60]}... | Tags: {tags} | Sentiment: {sentiment_score} | Entities: {entities}")
            except Exception as e:
                print(f"❌ Error inserting: {title[:60]} — {e}")

conn.commit()
cur.close()
conn.close()
print("✅ Feed parsing complete.")
