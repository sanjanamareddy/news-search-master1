CREATE TABLE articles (
  id SERIAL PRIMARY KEY,
  title TEXT,
  link TEXT UNIQUE,
  summary TEXT,
  published TIMESTAMP,
  source TEXT
);
