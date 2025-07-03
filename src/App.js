import React, { useState } from "react";
import axios from "axios";

function App() {
  const [query, setQuery] = useState("");
  const [articles, setArticles] = useState([]);

  const handleSearch = async (e) => {
    e.preventDefault();
    try {
      const res = await axios.get(`http://localhost:8000/search?query=${query}`);
      setArticles(res.data);
    } catch (err) {
      console.error("Search failed:", err);
    }
  };

  const renderTags = (items) =>
    items?.split(",").map((item, index) => (
      <span
        key={index}
        style={{
          backgroundColor: "#eef2ff",
          color: "#1e40af",
          padding: "2px 8px",
          margin: "2px",
          borderRadius: "12px",
          fontSize: "0.8rem",
          display: "inline-block",
        }}
      >
        {item.trim()}
      </span>
    ));

  return (
    <div style={{ padding: "2rem", fontFamily: "Arial" }}>
      <h2>📰 Finance News Search</h2>
      <form onSubmit={handleSearch}>
        <input
          type="text"
          value={query}
          placeholder="Search finance news..."
          onChange={(e) => setQuery(e.target.value)}
          style={{ padding: "0.5rem", width: "300px" }}
        />
        <button type="submit" style={{ padding: "0.5rem", marginLeft: "0.5rem" }}>
          Search
        </button>
      </form>

      <div style={{ marginTop: "2rem" }}>
        {articles.length === 0 && <p>No articles yet. Try searching!</p>}
        {articles.map((article, i) => (
          <div
            key={i}
            style={{
              borderBottom: "1px solid #ccc",
              paddingBottom: "1.5rem",
              marginBottom: "1.5rem",
            }}
          >
            {/* Header Row */}
            <div style={{ display: "flex", justifyContent: "space-between", gap: "1rem" }}>
              <div style={{ flex: 1 }}>
                <h3>
                  <a href={article.link} target="_blank" rel="noreferrer">
                    {article.title}
                  </a>
                </h3>
                <small>
                  <i>{new Date(article.published).toLocaleString()}</i>
                </small>
                <br />
                <small>
                  <b>Source:</b> {article.source}
                </small>
              </div>

              <div style={{ flex: 2 }}>
                <p>{article.summary}</p>

                {/* Tags */}
                <p style={{ fontSize: "0.9rem", color: "#444", marginTop: "1rem", marginBottom: "0.3rem" }}>
                  <b>Tags:</b>
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", marginBottom: "0.5rem" }}>
                  {renderTags(article.tags)}
                </div>

                {/* Entities */}
                <p style={{ fontSize: "0.9rem", color: "#444", marginBottom: "0.3rem" }}>
                  <b>Entities:</b>
                </p>
                <div style={{ display: "flex", flexWrap: "wrap", marginBottom: "0.5rem" }}>
                  {renderTags(article.entities)}
                </div>

                {/* Sentiment */}
                <p style={{ fontSize: "0.9rem", color: "#444" }}>
                  <b>Sentiment Score:</b>{" "}
                  {article.sentiment_score !== null ? (
                    <span
                      style={{
                        fontWeight: "bold",
                        color:
                          article.sentiment_score >= 4
                            ? "green"
                            : article.sentiment_score <= 2
                            ? "red"
                            : "orange",
                      }}
                    >
                      {article.sentiment_score} / 5
                    </span>
                  ) : (
                    <span style={{ color: "#999" }}>Not analyzed</span>
                  )}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
