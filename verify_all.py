"""
verify_all.py — Comprehensive End-to-End Master Health & Verification Suite
Tests configurations, database schemas, hybrid retrieval, tool dispatch, unit tests,
16 golden evaluations, and FastAPI HTTP/SSE endpoints in a single command.

Usage:
    python verify_all.py
"""

import sys
import time
import traceback
from pathlib import Path

# Ensure project root is in sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

PASS_LIST = []
FAIL_LIST = []


def run_gate(gate_name: str, test_fn):
    console.print(f"\n[bold cyan]▶ Checking Gate: {gate_name}[/bold cyan]")
    t0 = time.perf_counter()
    try:
        test_fn()
        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        PASS_LIST.append((gate_name, elapsed))
        console.print(f"  [bold green]✔ PASS[/bold green] — {gate_name} ({elapsed}ms)")
    except Exception as e:
        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        FAIL_LIST.append((gate_name, str(e), elapsed))
        console.print(f"  [bold red]✘ FAIL[/bold red] — {gate_name} ({elapsed}ms): {e}")
        traceback.print_exc()


# ── Gate 1: Config & Environment ─────────────────────────────────────────────
def test_gate_1_config():
    from app.config import settings

    assert settings.project_root.exists(), "project_root path does not exist"
    assert settings.data_dir.exists(), "data_dir does not exist"
    assert settings.docs_dir.exists(), "docs_dir does not exist"
    assert settings.max_tool_rounds == 6, f"unexpected max_tool_rounds: {settings.max_tool_rounds}"
    assert len(list(settings.docs_dir.glob("*.md"))) >= 8, "Expected at least 8 markdown docs"


# ── Gate 2: Database & FTS5 Indexing ──────────────────────────────────────────
def test_gate_2_database():
    from app.db.database import get_db_connection, init_db

    init_db()
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [r["name"] for r in cur.fetchall()]

    required_tables = [
        "conversations",
        "messages",
        "agent_runs",
        "tool_traces",
        "ticket_drafts",
        "pr_summaries",
        "idempotency_records",
    ]
    for req in required_tables:
        assert req in tables, f"Missing database table: {req}"

    # Verify FTS5 virtual table
    cur.execute("SELECT count(*) as cnt FROM docs_fts;")
    fts_cnt = cur.fetchone()["cnt"]
    assert fts_cnt >= 8, f"docs_fts has insufficient indexed docs: {fts_cnt}"
    conn.close()


# ── Gate 3: Tool Execution & Allowlist ────────────────────────────────────────
def test_gate_3_tools():
    import uuid
    from app.tools.implementations import (
        create_ticket_draft,
        get_pr,
        get_service,
        list_open_prs,
        list_tickets,
        search_docs,
        summarize_pr,
    )
    from app.tools.registry import TOOL_DEFINITIONS, dispatch_tool

    # 1. search_docs
    res_s = search_docs("latency spikes circuit breaker", top_k=2)
    assert res_s["count"] > 0, "search_docs returned 0 results"

    # 2. get_service
    res_svc = get_service("checkout-api")
    assert res_svc["found"] is True
    assert res_svc["service"]["slo_availability"] == 99.95

    # 3. list_open_prs & get_pr
    res_prs = list_open_prs()
    assert res_prs["count"] >= 3
    res_pr1 = get_pr(101)
    assert res_pr1["found"] is True

    # 4. list_tickets
    res_tk = list_tickets()
    assert res_tk["count"] >= 4

    # 5. create_ticket_draft with idempotency
    u_title = f"Test incident ticket {uuid.uuid4().hex[:6]}"
    res_draft = create_ticket_draft(
        title=u_title,
        description="Automated audit test incident payload",
        priority="P2",
        team="payments"
    )
    assert res_draft["status"] == "DRAFT_CREATED"

    # 6. summarize_pr
    res_sum = summarize_pr(
        pr_number=101,
        summary="Automated verification test PR summary",
        risk_level="MEDIUM",
        risk_notes="Canary verification required"
    )
    assert res_sum["status"] in ("RECORD_CREATED", "SUMMARY_ALREADY_EXISTS")

    # 7. Disallowed tool check
    bad_res = dispatch_tool("unauthorized_tool_delete_everything", {})
    assert bad_res["ok"] is False
    assert "Security Error" in bad_res["error"]


# ── Gate 4: Unit Test Suite ───────────────────────────────────────────────────
def test_gate_4_pytest():
    import pytest

    retcode = pytest.main(["-q", "tests/"])
    assert retcode == 0, f"pytest tests failed with exit code: {retcode}"


# ── Gate 5: Golden Benchmark Evaluations (16 Cases) ──────────────────────────
def test_gate_5_golden_evals():
    import json
    from app.agent.orchestrator import PulseOpsOrchestrator
    from app.config import settings
    from evals.graders import grade_case

    cases_file = settings.project_root / "evals" / "cases.jsonl"
    assert cases_file.exists(), "cases.jsonl does not exist"

    orchestrator = PulseOpsOrchestrator(mode="mock")
    cases = []
    with open(cases_file, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                cases.append(json.loads(line))

    assert len(cases) >= 16, f"Expected >= 16 golden cases, got {len(cases)}"

    passed = 0
    for c in cases:
        conv_id = f"verify_{c['id']}"
        res = orchestrator.run_turn(conv_id, c["prompt"])
        is_pass, failures = grade_case(c, res)
        assert is_pass, f"Golden case {c['id']} failed: {failures}"
        passed += 1

    assert passed == len(cases)


# ── Gate 6: FastAPI HTTP & Streaming Endpoints ────────────────────────────────
def test_gate_6_fastapi():
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # Health
    r_h = client.get("/api/health")
    assert r_h.status_code == 200
    assert r_h.json()["status"] == "healthy"

    # Catalog
    r_svc = client.get("/api/services")
    assert r_svc.status_code == 200
    assert r_svc.json()["count"] >= 6

    # Tickets All
    r_tk = client.get("/api/tickets/all")
    assert r_tk.status_code == 200
    assert r_tk.json()["count"] >= 4

    # Chat Standard
    r_chat = client.post("/api/chat", json={
        "conversation_id": "verify_chat",
        "message": "What is the availability SLO for checkout-api?",
        "mode": "mock"
    })
    assert r_chat.status_code == 200
    assert "99.95" in r_chat.json()["response"]

    # Chat Stream (SSE)
    r_stream = client.post("/api/chat/stream", json={
        "conversation_id": "verify_stream",
        "message": "List open PRs",
        "mode": "mock"
    })
    assert r_stream.status_code == 200
    assert "text/event-stream" in r_stream.headers.get("content-type", "")

    # Static UI Home
    r_ui = client.get("/")
    assert r_ui.status_code == 200
    assert "PulseOps" in r_ui.text


def main():
    console.print(
        Panel.fit(
            "[bold cyan]⚡ PulseOps End-to-End Master Verification Suite[/bold cyan]\n"
            "[dim]Testing config, DB, FTS5, tools, pytest, 16 evals, and FastAPI SSE[/dim]",
            border_style="cyan"
        )
    )

    t_start = time.perf_counter()

    run_gate("Gate 1: Config & Directories", test_gate_1_config)
    run_gate("Gate 2: SQLite Schema & FTS5 Indexing", test_gate_2_database)
    run_gate("Gate 3: Tool Inventory & Allowlist", test_gate_3_tools)
    run_gate("Gate 4: Pytest Unit Test Suite", test_gate_4_pytest)
    run_gate("Gate 5: Golden Eval Harness (16/16)", test_gate_5_golden_evals)
    run_gate("Gate 6: FastAPI HTTP REST & SSE Streaming", test_gate_6_fastapi)

    t_total = round(time.perf_counter() - t_start, 2)

    console.print("\n" + "=" * 60)
    summary_table = Table(title="Verification Summary", show_header=True, header_style="bold blue")
    summary_table.add_column("Verification Gate", style="bold")
    summary_table.add_column("Status", style="bold")
    summary_table.add_column("Latency", style="dim")

    for name, el in PASS_LIST:
        summary_table.add_row(name, "[green]PASSED[/green]", f"{el}ms")
    for name, err, el in FAIL_LIST:
        summary_table.add_row(name, f"[red]FAILED: {err}[/red]", f"{el}ms")

    console.print(summary_table)

    if FAIL_LIST:
        console.print(f"\n[bold red]❌ {len(FAIL_LIST)} verification gates failed.[/bold red]")
        sys.exit(1)
    else:
        console.print(f"\n[bold green]🎉 ALL 6 GATES PASSED! Total time: {t_total}s[/bold green]\n")


if __name__ == "__main__":
    main()
