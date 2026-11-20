import pytest
from fastapi.testclient import TestClient
from app.db.database import init_db
from app.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_db():
    init_db()


def test_health_endpoint():
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True


def test_chat_endpoint_mock_mode():
    res = client.post("/api/chat", json={
        "conversation_id": "api_test_conv",
        "message": "What is the availability SLO for checkout-api?",
        "mode": "mock"
    })
    assert res.status_code == 200
    data = res.json()
    assert "99.95" in data["response"]
    assert len(data["tool_traces"]) >= 1
    assert data["tool_traces"][0]["tool_name"] == "get_service"


def test_chat_refusal_endpoint():
    res = client.post("/api/chat", json={
        "conversation_id": "api_test_refusal",
        "message": "Post this outage to our public company Twitter/X account",
        "mode": "mock"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["refusal_triggered"] is True
    assert "Policy Refusal" in data["response"]


def test_list_tickets_and_summaries():
    res_t = client.get("/api/tickets")
    assert res_t.status_code == 200
    assert "tickets" in res_t.json()

    res_p = client.get("/api/prs/summaries")
    assert res_p.status_code == 200
    assert "summaries" in res_p.json()


def test_traces_endpoint():
    res = client.get("/api/traces/api_test_conv")
    assert res.status_code == 200
    data = res.json()
    assert data["conversation_id"] == "api_test_conv"
    assert data["count"] >= 1
