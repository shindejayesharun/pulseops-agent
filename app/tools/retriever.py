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
    High-performance full-text search using SQLite FTS5 with BM25 ranking.
    Optimal for synthetic and medium-scale corpora (6-100 documents) with zero external infrastructure.
    """

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        conn = get_db_connection()
        cur = conn.cursor()

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


class HybridRRFRetriever(BaseRetriever):
    """
    Hybrid retriever fusing SQLite FTS5 BM25 search with token-overlap ranking
    using Reciprocal Rank Fusion (RRF: 1 / (60 + rank)).
    """

    def __init__(self, fts_retriever: BaseRetriever = None):
        self.fts_retriever = fts_retriever or SQLiteFTS5Retriever()

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        # 1. Primary Lexical FTS5 Results
        fts_results = self.fts_retriever.search(query, top_k=top_k * 2)

        # 2. Token overlap ranking across all indexed documents
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT doc_id, title, path, content FROM docs_fts")
        all_docs = cur.fetchall()
        conn.close()

        query_terms = set(re.findall(r"\w+", query.lower()))
        overlap_scores = []
        for d in all_docs:
            doc_terms = set(re.findall(r"\w+", d["content"].lower()))
            overlap = len(query_terms.intersection(doc_terms))
            overlap_scores.append((overlap, d))

        overlap_scores.sort(key=lambda x: x[0], reverse=True)

        # 3. Reciprocal Rank Fusion (RRF k=60)
        rrf_scores: Dict[str, float] = {}
        doc_map: Dict[str, Dict[str, Any]] = {}

        for rank, item in enumerate(fts_results):
            doc_id = item["doc_id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (60 + rank))
            doc_map[doc_id] = item

        for rank, (_, row) in enumerate(overlap_scores[: top_k * 2]):
            doc_id = row["doc_id"]
            rrf_scores[doc_id] = rrf_scores.get(doc_id, 0.0) + (1.0 / (60 + rank))
            if doc_id not in doc_map:
                doc_map[doc_id] = {
                    "doc_id": row["doc_id"],
                    "title": row["title"],
                    "path": row["path"],
                    "snippet": row["content"][:200] + "...",
                    "excerpt": row["content"][:500] + "...",
                    "score": 0.0
                }

        # 4. Sort by RRF score descending
        fused = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)
        final_results = []
        for doc_id, rrf_val in fused[:top_k]:
            item = doc_map[doc_id]
            item["score"] = round(rrf_val, 4)
            final_results.append(item)

        return final_results


import re

retriever = HybridRRFRetriever()
