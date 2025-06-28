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
        display: "flex",
        justifyContent: "space-between",
        gap: "1rem",
        borderBottom: "1px solid #ccc",
        paddingBottom: "1rem",
        marginBottom: "1.5rem",
      }}
    >
      {/* Left column: Title, Date, Source */}
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

      {/* Right column: Summary */}
      <div style={{ flex: 2 }}>
        <p>{article.summary?.slice(0, 400)}...</p>
      </div>
    </div>
  ))}
</div>

    </div>
  );
}

export default App;