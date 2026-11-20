import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from app.db.database import get_db_connection
from app.db.models import AgentRun, Conversation, Message, PRSummary, TicketDraft, ToolTrace


def _get_utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Repository:
    def __init__(self, db_conn=None):
        self._custom_conn = db_conn

    def _conn(self):
        return self._custom_conn if self._custom_conn is not None else get_db_connection()

    # --- Conversations ---
    def create_conversation(self, conversation_id: Optional[str] = None, user_label: Optional[str] = None) -> str:
        conv_id = conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
        now = _get_utc_now()
        conn = self._conn()
        with conn:
            conn.execute(
                "INSERT INTO conversations (id, user_label, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (conv_id, user_label or "Operations Chat", now, now)
            )
        return conv_id

    def get_conversation(self, conv_id: str) -> Optional[Dict[str, Any]]:
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM conversations WHERE id = ?", (conv_id,))
        row = cur.fetchone()
        return dict(row) if row else None

    def list_conversations(self, limit: int = 20) -> List[Dict[str, Any]]:
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM conversations ORDER BY updated_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

    # --- Messages ---
    def add_message(self, conversation_id: str, role: str, content: str) -> str:
        msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        now = _get_utc_now()
        conn = self._conn()
        with conn:
            conn.execute(
                "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (msg_id, conversation_id, role, content, now)
            )
            conn.execute(
                "UPDATE conversations SET updated_at = ? WHERE id = ?",
                (now, conversation_id)
            )
        return msg_id

    def get_messages(self, conversation_id: str) -> List[Dict[str, Any]]:
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM messages WHERE conversation_id = ? ORDER BY created_at ASC", (conversation_id,))
        return [dict(r) for r in cur.fetchall()]

    # --- Agent Runs ---
    def record_agent_run(
        self,
        conversation_id: str,
        provider: str,
        model: str,
        status: str,
        prompt_tokens: int = 0,
        completion_tokens: int = 0,
        duration_ms: float = 0.0,
        run_id: Optional[str] = None
    ) -> str:
        r_id = run_id or f"run_{uuid.uuid4().hex[:12]}"
        now = _get_utc_now()
        conn = self._conn()
        with conn:
            conn.execute(
                """INSERT INTO agent_runs 
                (id, conversation_id, provider, model, status, prompt_tokens, completion_tokens, duration_ms, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (r_id, conversation_id, provider, model, status, prompt_tokens, completion_tokens, duration_ms, now)
            )
        return r_id

    def update_agent_run(self, run_id: str, status: str, duration_ms: float) -> None:
        conn = self._conn()
        with conn:
            conn.execute(
                "UPDATE agent_runs SET status = ?, duration_ms = ? WHERE id = ?",
                (status, duration_ms, run_id)
            )

    # --- Tool Traces ---
    def record_tool_trace(
        self,
        conversation_id: str,
        step_number: int,
        tool_name: str,
        args_json: Dict[str, Any],
        result_json: Any,
        ok: bool = True,
        latency_ms: float = 0.0,
        run_id: Optional[str] = None
    ) -> str:
        trace_id = f"trc_{uuid.uuid4().hex[:12]}"
        now = _get_utc_now()
        conn = self._conn()
        with conn:
            conn.execute(
                """INSERT INTO tool_traces 
                (id, conversation_id, run_id, step_number, tool_name, args_json, result_json, ok, latency_ms, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    trace_id,
                    conversation_id,
                    run_id,
                    step_number,
                    tool_name,
                    json.dumps(args_json),
                    json.dumps(result_json) if not isinstance(result_json, str) else result_json,
                    1 if ok else 0,
                    latency_ms,
                    now
                )
            )
        return trace_id

    def get_tool_traces(self, conversation_id: str) -> List[Dict[str, Any]]:
        conn = self._conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM tool_traces WHERE conversation_id = ? ORDER BY step_number ASC, created_at ASC",
            (conversation_id,)
        )
        rows = cur.fetchall()
        traces = []
        for r in rows:
            d = dict(r)
            try:
                d["args_json"] = json.loads(d["args_json"])
            except Exception:
                pass
            try:
                d["result_json"] = json.loads(d["result_json"])
            except Exception:
                pass
            d["ok"] = bool(d["ok"])
            traces.append(d)
        return traces

    # --- Ticket Drafts (HITL Artifacts) ---
    def create_ticket_draft(
        self,
        title: str,
        description: str,
        priority: str,
        team: str,
        labels: List[str],
        service_id: Optional[str] = None,
        source_conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        draft_id = f"TICK-DRAFT-{uuid.uuid4().hex[:6].upper()}"
        now = _get_utc_now()
        conn = self._conn()
        with conn:
            conn.execute(
                """INSERT INTO ticket_drafts 
                (id, source_conversation_id, service_id, title, description, priority, team, labels_json, status, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'DRAFT_PENDING_APPROVAL', ?)""",
                (draft_id, source_conversation_id, service_id, title, description, priority, team, json.dumps(labels), now)
            )
        return {
            "id": draft_id,
            "title": title,
            "description": description,
            "priority": priority,
            "team": team,
            "labels": labels,
            "service_id": service_id,
            "status": "DRAFT_PENDING_APPROVAL",
            "created_at": now
        }

    def list_ticket_drafts(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM ticket_drafts ORDER BY created_at DESC LIMIT ?", (limit,))
        rows = cur.fetchall()
        results = []
        for r in rows:
            d = dict(r)
            try:
                d["labels"] = json.loads(d["labels_json"])
            except Exception:
                d["labels"] = []
            results.append(d)
        return results

    # --- PR Summaries ---
    def create_pr_summary(
        self,
        pr_number: int,
        summary: str,
        risk_level: str,
        risk_notes: str,
        source_conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        summary_id = f"PR-SUM-{uuid.uuid4().hex[:6].upper()}"
        now = _get_utc_now()
        conn = self._conn()
        with conn:
            conn.execute(
                """INSERT INTO pr_summaries 
                (id, source_conversation_id, pr_number, summary, risk_level, risk_notes, created_at) 
                VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (summary_id, source_conversation_id, pr_number, summary, risk_level, risk_notes, now)
            )
        return {
            "id": summary_id,
            "pr_number": pr_number,
            "summary": summary,
            "risk_level": risk_level,
            "risk_notes": risk_notes,
            "created_at": now
        }

    def list_pr_summaries(self, limit: int = 50) -> List[Dict[str, Any]]:
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM pr_summaries ORDER BY created_at DESC LIMIT ?", (limit,))
        return [dict(r) for r in cur.fetchall()]

    # --- Idempotency ---
    def check_idempotency(self, key: str) -> Optional[Dict[str, Any]]:
        conn = self._conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM idempotency_records WHERE key = ?", (key,))
        row = cur.fetchone()
        return dict(row) if row else None

    def record_idempotency(self, key: str, action_type: str, artifact_id: str) -> None:
        now = _get_utc_now()
        conn = self._conn()
        with conn:
            conn.execute(
                "INSERT OR REPLACE INTO idempotency_records (key, action_type, artifact_id, created_at) VALUES (?, ?, ?, ?)",
                (key, action_type, artifact_id, now)
            )


repo = Repository()
