import json
import sqlite3
from pathlib import Path
from typing import Optional
from app.config import settings


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    target_path = db_path or settings.db_path
    conn = sqlite3.connect(str(target_path), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    conn = get_db_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS conversations (
            id TEXT PRIMARY KEY,
            user_label TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS messages (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            role TEXT CHECK(role IN ('user', 'assistant', 'system', 'tool')) NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS agent_runs (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            provider TEXT NOT NULL,
            model TEXT NOT NULL,
            status TEXT NOT NULL,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            duration_ms REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tool_traces (
            id TEXT PRIMARY KEY,
            conversation_id TEXT NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
            run_id TEXT REFERENCES agent_runs(id),
            step_number INTEGER NOT NULL,
            tool_name TEXT NOT NULL,
            args_json TEXT NOT NULL,
            result_json TEXT NOT NULL,
            ok BOOLEAN NOT NULL DEFAULT 1,
            latency_ms REAL NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ticket_drafts (
            id TEXT PRIMARY KEY,
            source_conversation_id TEXT REFERENCES conversations(id),
            service_id TEXT,
            title TEXT NOT NULL,
            description TEXT NOT NULL,
            priority TEXT NOT NULL,
            team TEXT NOT NULL,
            labels_json TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'DRAFT_PENDING_APPROVAL',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS pr_summaries (
            id TEXT PRIMARY KEY,
            source_conversation_id TEXT REFERENCES conversations(id),
            pr_number INTEGER NOT NULL,
            summary TEXT NOT NULL,
            risk_level TEXT NOT NULL,
            risk_notes TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS idempotency_records (
            key TEXT PRIMARY KEY,
            action_type TEXT NOT NULL,
            artifact_id TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_messages_conv ON messages(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_traces_conv ON tool_traces(conversation_id);
        CREATE INDEX IF NOT EXISTS idx_drafts_team ON ticket_drafts(team);
        """)

        # FTS5 Virtual Table for Markdown Documents
        conn.execute("""
        CREATE VIRTUAL TABLE IF NOT EXISTS docs_fts USING fts5(
            doc_id UNINDEXED,
            title,
            path,
            content,
            tokenize='porter unicode61'
        );
        """)

    conn.close()
    index_documents_if_needed(db_path)


def index_documents_if_needed(db_path: Optional[Path] = None) -> None:
    conn = get_db_connection(db_path)
    cur = conn.cursor()
    cur.execute("SELECT count(*) as cnt FROM docs_fts;")
    row = cur.fetchone()
    count = row["cnt"] if row else 0

    if count > 0:
        conn.close()
        return

    docs_dir = settings.docs_dir
    if not docs_dir.exists():
        conn.close()
        return

    with conn:
        for doc_file in docs_dir.glob("*.md"):
            try:
                content = doc_file.read_text(encoding="utf-8")
                # Extract first markdown header as title if available
                title = doc_file.stem.replace("_", " ").title()
                for line in content.splitlines():
                    if line.startswith("# "):
                        title = line[2:].strip()
                        break

                rel_path = f"data/docs/{doc_file.name}"
                conn.execute(
                    "INSERT INTO docs_fts (doc_id, title, path, content) VALUES (?, ?, ?, ?);",
                    (doc_file.name, title, rel_path, content)
                )
            except Exception as e:
                print(f"Warning: Failed to index {doc_file}: {e}")

    conn.close()
