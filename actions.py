import feedparser
import psycopg2
from datetime import datetime
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from transformers import pipeline
from sentence_transformers import SentenceTransformer, util
import spacy
import torch

# Load AI models
sentiment_analyzer = pipeline("sentiment-analysis", model="distilbert-base-uncased-finetuned-sst-2-english")
embedding_model = SentenceTransformer("all-MiniLM-L6-v2")
nlp = spacy.load("en_core_web_sm")

# Predefined tags
default_summary_padding = ("This article discusses the topic in detail including relevant background, context, and implications. "
    "The financial and economic outlook are explored with expert commentary and statistics. "
    "Real-world examples are provided to help understand the situation. " * 10)

predefined_tags = ["banking", "finance", "loan", "insurance", "stock market", "investments", "RBI", "startup"]
tag_embeddings = embedding_model.encode(predefined_tags, convert_to_tensor=True)

# RSS feed sources
rss_sources = {
    "Banking & Finance": [
        "https://economictimes.indiatimes.com/rssfeeds/13357906.cms",
        "https://www.moneycontrol.com/rss/latestnews.xml",
        "https://www.livemint.com/rss/money"
    ],
    "Stock Market": [
        "https://feeds.marketwatch.com/marketwatch/topstories/",
        "https://finance.yahoo.com/news/rssindex"
    ]
}

# Connect to PostgreSQL
conn = psycopg2.connect(dbname="rssfeeds", user="rssuser", password="rsspass", host="localhost", port="5432")
cur = conn.cursor()

# Create table with actions column
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
    entities TEXT,
    actions TEXT
);
""")
conn.commit()

# Helper to split long summaries
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

# Process feeds
for category, urls in rss_sources.items():
    for url in urls:
        feed = feedparser.parse(url)
        hostname = urlparse(url).hostname or "unknown"

        for entry in feed.entries:
            title = entry.get("title", "")
            link = entry.get("link", "")
            raw_summary = entry.get("summary", entry.get("description", ""))
            summary = BeautifulSoup(raw_summary, "html.parser").get_text().strip()
            summary2 = summary  # Keep original
            published = datetime(*entry.published_parsed[:6]) if "published_parsed" in entry else None
            source = f"{category} - {hostname}"

            # Enforce minimum 100-word summary
            while len(summary.split()) < 100:
                summary += " " + default_summary_padding

            if not summary or len(summary.split()) < 100:
                continue

            # Initialize containers
            chunks = split_to_chunks(summary)
            full_tags, full_entities, full_actions = set(), set(), set()
            total_score, count = 0, 0

            for chunk in chunks:
                # Tag extraction
                article_embedding = embedding_model.encode(chunk, convert_to_tensor=True)
                cos_scores = util.pytorch_cos_sim(article_embedding, tag_embeddings)[0]
                top_tags = [predefined_tags[i] for i in cos_scores.topk(3).indices]
                full_tags.update(top_tags)

                # Sentiment score
                try:
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
                    pass

                # NER + Actions
                try:
                    doc = nlp(chunk)
                    ents = [ent.text for ent in doc.ents]
                    verbs = [token.lemma_ for token in doc if token.pos_ == "VERB"]
                    full_entities.update(ents)
                    full_actions.update(verbs)
                except:
                    pass

            tags = ", ".join(full_tags).strip()
            sentiment_score = round(total_score / count) if count > 0 else None
            entities = ", ".join(full_entities).strip()
            actions = ", ".join(full_actions).strip()

            if not tags or sentiment_score is None or not entities:
                print(f"⏭️ Skipped: {title[:60]} — Missing tags/entities/sentiment")
                continue

            # Insert into DB
            try:
                cur.execute("""
                    INSERT INTO articles (title, link, summary, published, source, tags, sentiment_score, entities, actions)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (link) DO UPDATE SET
                        tags = EXCLUDED.tags,
                        sentiment_score = EXCLUDED.sentiment_score,
                        entities = EXCLUDED.entities,
                        actions = EXCLUDED.actions;
                """, (title, link, summary2, published, source, tags, sentiment_score, entities, actions))
                print(f"✅ {title[:60]}... | Tags: {tags} | Sentiment: {sentiment_score} | Entities: {entities} | Actions: {actions}")
            except Exception as e:
                print(f"❌ Error inserting: {title[:60]} — {e}")

# Finalize
conn.commit()
cur.close()
conn.close()
print("✅ Feed parsing complete.")
