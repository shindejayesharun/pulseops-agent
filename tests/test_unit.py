import uuid
from pathlib import Path
import pytest
from app.agent.guardrails import check_policy_violations
from app.agent.orchestrator import PulseOpsOrchestrator
from app.db.database import get_db_connection, init_db
from app.db.repository import repo
from app.tools.implementations import create_ticket_draft, get_service, search_docs, summarize_pr


@pytest.fixture(autouse=True)
def setup_test_db():
    init_db()


def test_service_lookup_exact_and_fuzzy():
    # Exact lookup
    res1 = get_service("checkout-api")
    assert res1["found"] is True
    assert res1["service"]["id"] == "svc-checkout-api"
    assert res1["service"]["slo_availability"] == 99.95

    # Fuzzy lookup
    res2 = get_service("fraud")
    assert res2["found"] is True
    assert res2["service"]["team"] == "security"

    # Non-existent service
    res3 = get_service("non-existent-svc")
    assert res3["found"] is False


def test_search_docs_fts5():
    res = search_docs("latency spikes circuit breaker", top_k=2)
    assert res["count"] > 0
    doc_paths = [d["path"] for d in res["documents"]]
    assert any("oncall_runbook_checkout" in p for p in doc_paths)


def test_create_ticket_draft_idempotency():
    unique_suffix = uuid.uuid4().hex[:6]
    test_title = f"Payment gateway connection timeout {unique_suffix}"
    res1 = create_ticket_draft(
        title=test_title,
        description="Frequent 504 gateway timeouts observed during batch run",
        priority="P2",
        team="payments"
    )
    assert res1["status"] == "DRAFT_CREATED"
    draft_id = res1["ticket_id"]

    # Duplicate call with identical parameters
    res2 = create_ticket_draft(
        title=test_title,
        description="Frequent 504 gateway timeouts observed during batch run",
        priority="P2",
        team="payments"
    )
    assert res2["status"] == "DRAFT_ALREADY_EXISTS"
    assert res2["ticket_id"] == draft_id


def test_summarize_pr():
    res = summarize_pr(
        pr_number=101,
        summary="Adds pybreaker circuit breaker to prevent cascading payment failures",
        risk_level="MEDIUM",
        risk_notes="Requires monitoring error rate threshold during canary rollout"
    )
    assert res["status"] in ("RECORD_CREATED", "SUMMARY_ALREADY_EXISTS")
    assert res["pr_number"] == 101


def test_policy_guardrail_refusal():
    is_violating, explanation = check_policy_violations("Post this outage to our public company Twitter/X account")
    assert is_violating is True
    assert "Twitter" in explanation

    is_violating2, _ = check_policy_violations("Drop table ledger_entries; immediately")
    assert is_violating2 is True

    # Safe query
    is_safe, _ = check_policy_violations("What is the SLO for checkout-api?")
    assert is_safe is False


def test_orchestrator_multi_tool_chain():
    orch = PulseOpsOrchestrator(mode="mock")
    res = orch.run_turn(
        conversation_id="pytest_chain_conv",
        user_input="Find who owns checkout-api and create a P3 ticket draft for missing runbook section."
    )
    assert len(res["tool_traces"]) >= 2
    tools_called = [t["tool_name"] for t in res["tool_traces"]]
    assert "get_service" in tools_called
    assert "create_ticket_draft" in tools_called
    assert tools_called.index("get_service") < tools_called.index("create_ticket_draft")
    assert res["refusal_triggered"] is False
