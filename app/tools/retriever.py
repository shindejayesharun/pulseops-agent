from abc import ABC, abstractmethod
from typing import Any, Dict, List
from app.config import settings
from app.db.database import get_db_connection


class BaseRetriever(ABC):
    """Abstract interface for documentation retrieval."""

    @abstractmethod
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Retrieve relevant documentation snippets for a given query."""
        pass


class SQLiteFTS5Retriever(BaseRetriever):
    """
    High-performance, explainable full-text search using SQLite FTS5 with BM25 ranking.
    Optimal for synthetic and medium-scale corpora (6-100 documents) with zero external infrastructure.
    """

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cur = conn.cursor()

        # Sanitize query for FTS5 syntax
        sanitized = "".join(c if c.isalnum() or c.isspace() else " " for c in query)
        terms = [t for t in sanitized.split() if len(t) > 1]
        if not terms:
            conn.close()
            return []

        fts_match = " OR ".join(f'"{t}"*' for t in terms)

        try:
            cur.execute("""
                SELECT doc_id, title, path, snippet(docs_fts, 3, '<b>', '</b>', '...', 32) as match_snippet,
                       bm25(docs_fts) as rank, content
                FROM docs_fts
                WHERE docs_fts MATCH ?
                ORDER BY rank
                LIMIT ?;
            """, (fts_match, top_k))
            rows = cur.fetchall()
            results = []
            for r in rows:
                results.append({
                    "doc_id": r["doc_id"],
                    "title": r["title"],
                    "path": r["path"],
                    "snippet": r["match_snippet"],
                    "excerpt": r["content"][:600] + ("..." if len(r["content"]) > 600 else ""),
                    "score": round(float(r["rank"]), 4)
                })
            conn.close()
            return results
        except Exception:
            # Fallback simple substring search if FTS syntax edge case arises
            conn.close()
            return self._fallback_substring_search(terms, top_k)

    def _fallback_substring_search(self, terms: List[str], top_k: int) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT doc_id, title, path, content FROM docs_fts")
        rows = cur.fetchall()
        scored = []
        for r in rows:
            content_lower = r["content"].lower()
            matches = sum(1 for t in terms if t.lower() in content_lower)
            if matches > 0:
                scored.append((matches, r))
        scored.sort(key=lambda x: x[0], reverse=True)
        results = []
        for _, r in scored[:top_k]:
            results.append({
                "doc_id": r["doc_id"],
                "title": r["title"],
                "path": r["path"],
                "snippet": r["content"][:200] + "...",
                "excerpt": r["content"][:500] + "...",
                "score": 1.0
            })
        conn.close()
        return results


retriever = SQLiteFTS5Retriever()
