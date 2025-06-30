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

  // Clean summary to remove image tags and unwanted HTML
  const cleanSummary = (html) => {
    const tmp = document.createElement("div");
    tmp.innerHTML = html;
    const imgs = tmp.getElementsByTagName("img");
    while (imgs.length > 0) {
      imgs[0].parentNode.removeChild(imgs[0]);
    }
    return tmp.textContent || tmp.innerText || "";
  };

  return (
    <div style={{ padding: "2rem", fontFamily: "Arial, sans-serif", backgroundColor: "#f9f9f9" }}>
      <h2>📰 Finance News Search</h2>

      {/* Search Box */}
      <form onSubmit={handleSearch} style={{ marginBottom: "2rem" }}>
        <input
          type="text"
          value={query}
          placeholder="Search finance news..."
          onChange={(e) => setQuery(e.target.value)}
          style={{
            padding: "0.5rem",
            width: "300px",
            borderRadius: "4px",
            border: "1px solid #ccc",
          }}
        />
        <button
          type="submit"
          style={{
            padding: "0.5rem 1rem",
            marginLeft: "0.5rem",
            backgroundColor: "#007BFF",
            color: "white",
            border: "none",
            borderRadius: "4px",
            cursor: "pointer",
          }}
        >
          Search
        </button>
      </form>

      {/* Results */}
      <div>
        {articles.length === 0 && <p>No articles yet. Try searching!</p>}
        {articles.map((article, i) => (
          <div
            key={i}
            style={{
              backgroundColor: "white",
              padding: "1rem",
              borderRadius: "8px",
              boxShadow: "0 2px 5px rgba(0,0,0,0.1)",
              marginBottom: "1.5rem",
              display: "flex",
              flexDirection: "row",
              justifyContent: "space-between",
              gap: "1rem",
            }}
          >
            {/* Left Column: Title, Date, Source */}
            <div style={{ flex: 1 }}>
              <h3 style={{ marginBottom: "0.5rem" }}>
                <a
                  href={article.link}
                  target="_blank"
                  rel="noreferrer"
                  style={{ color: "#007BFF", textDecoration: "none" }}
                >
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

            {/* Right Column: Summary, Tags, Sentiment */}
            <div style={{ flex: 2 }}>
              <p>{cleanSummary(article.summary)?.slice(0, 400)}...</p>

              {/* Tags */}
              <p style={{ marginTop: "0.5rem", fontSize: "0.9rem", color: "#444" }}>
                <b>Tags:</b>{" "}
                {article.tags && article.tags.trim() !== "" ? (
                  <i>{article.tags}</i>
                ) : (
                  <span style={{ color: "#999" }}>No tags available</span>
                )}
              </p>

              {/* Sentiment Score */}
              <p style={{ fontSize: "0.9rem", color: "#444" }}>
                <b>Sentiment Score:</b>{" "}
                {article.sentiment_score !== null && article.sentiment_score !== undefined ? (
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

              {/* Named Entities */}
              <p style={{ fontSize: "0.9rem", color: "#444" }}>
                <b>Entities:</b>{" "}
                {article.entities && article.entities.trim() !== "" ? (
                  <i>{article.entities}</i>
                ) : (
                  <span style={{ color: "#999" }}>No entities extracted</span>
                )}
              </p>

            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
