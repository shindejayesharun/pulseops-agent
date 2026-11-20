import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.config import settings
from app.db.repository import repo
from app.tools.retriever import retriever
from app.tools.schemas import (
    CreateTicketDraftInput,
    GetPRInput,
    GetServiceInput,
    ListOpenPRsInput,
    ListTicketsInput,
    SearchDocsInput,
    SummarizePRInput,
)


def _load_json_data(filename: str) -> List[Dict[str, Any]]:
    target = settings.data_dir / filename
    if not target.exists():
        return []
    with open(target, "r", encoding="utf-8") as f:
        return json.load(f)


# --- Tool 1: search_docs ---
def search_docs(query: str, top_k: int = 3) -> Dict[str, Any]:
    """Search internal engineering documentation and runbooks for answers and triage instructions."""
    validated = SearchDocsInput(query=query, top_k=top_k)
    results = retriever.search(validated.query, top_k=validated.top_k)
    return {
        "query": validated.query,
        "count": len(results),
        "documents": results,
    }


# --- Tool 2: get_service ---
def get_service(service_name_or_id: str) -> Dict[str, Any]:
    """Retrieve detailed service inventory metadata, owner team, SLO, on-call handle, and dependencies."""
    validated = GetServiceInput(service_name_or_id=service_name_or_id)
    target = validated.service_name_or_id.strip().lower()
    services = _load_json_data("services.json")

    # 1. Exact match by id or name
    for s in services:
        if s["id"].lower() == target or s["name"].lower() == target:
            return {"found": True, "service": s}

    # 2. Fuzzy substring match
    for s in services:
        if target in s["id"].lower() or target in s["name"].lower():
            return {"found": True, "service": s}

    return {
        "found": False,
        "error": f"Service '{service_name_or_id}' not found in Northstar service catalog.",
        "available_services": [s["name"] for s in services]
    }


# --- Tool 3: list_open_prs ---
def list_open_prs(service_id: Optional[str] = None) -> Dict[str, Any]:
    """List open pull requests with authors, file changes, and risk ratings, optionally filtered by service."""
    validated = ListOpenPRsInput(service_id=service_id)
    prs = _load_json_data("prs.json")
    open_prs = [p for p in prs if p.get("status") == "open"]

    if validated.service_id:
        target_svc = validated.service_id.strip().lower()
        open_prs = [p for p in open_prs if target_svc in p.get("service_id", "").lower()]

    return {
        "count": len(open_prs),
        "prs": [
            {
                "number": p["number"],
                "title": p["title"],
                "author": p["author"],
                "service_id": p["service_id"],
                "risk_level": p.get("risk_level", "UNKNOWN"),
                "description": p.get("description", "")
            }
            for p in open_prs
        ]
    }


# --- Tool 4: get_pr ---
def get_pr(pr_number: int) -> Dict[str, Any]:
    """Fetch complete metadata, author, files changed, and diff summary for a specific pull request."""
    validated = GetPRInput(pr_number=pr_number)
    prs = _load_json_data("prs.json")
    for p in prs:
        if p["number"] == validated.pr_number:
            return {"found": True, "pr": p}

    return {
        "found": False,
        "error": f"Pull request #{validated.pr_number} was not found."
    }


# --- Tool 5: create_ticket_draft (HITL Safe Write) ---
def create_ticket_draft(
    title: str,
    description: str,
    priority: str,
    team: str,
    labels: Optional[List[str]] = None,
    service_id: Optional[str] = None,
    conversation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a local ticket draft for human review. Never publishes to external Jira/production systems."""
    validated = CreateTicketDraftInput(
        title=title,
        description=description,
        priority=priority,
        team=team,
        labels=labels or [],
        service_id=service_id
    )

    # Idempotency deduplication check
    raw_key = f"ticket:{validated.team}:{validated.priority}:{validated.title}".lower()
    idemp_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    cached = repo.check_idempotency(idemp_key)
    if cached:
        return {
            "status": "DRAFT_ALREADY_EXISTS",
            "ticket_id": cached["artifact_id"],
            "title": validated.title,
            "priority": validated.priority,
            "team": validated.team,
            "message": "A draft ticket with these exact parameters already exists (idempotency preserved)."
        }

    draft = repo.create_ticket_draft(
        title=validated.title,
        description=validated.description,
        priority=validated.priority,
        team=validated.team,
        labels=validated.labels,
        service_id=validated.service_id,
        source_conversation_id=conversation_id
    )
    repo.record_idempotency(idemp_key, "ticket_draft", draft["id"])

    return {
        "status": "DRAFT_CREATED",
        "ticket_id": draft["id"],
        "title": draft["title"],
        "priority": draft["priority"],
        "team": draft["team"],
        "hitl_policy": "Draft persisted locally. Awaiting human confirmation before dispatch.",
        "message": f"Successfully created local ticket draft {draft['id']} (Priority: {draft['priority']}, Team: {draft['team']})."
    }


# --- Tool 6: summarize_pr (HITL Safe Write) ---
def summarize_pr(
    pr_number: int,
    summary: str,
    risk_level: str,
    risk_notes: str,
    conversation_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Produce and persist a structured PR summary with risk assessment and rollback notes."""
    validated = SummarizePRInput(
        pr_number=pr_number,
        summary=summary,
        risk_level=risk_level,
        risk_notes=risk_notes
    )

    raw_key = f"pr_sum:{validated.pr_number}:{validated.risk_level}".lower()
    idemp_key = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    cached = repo.check_idempotency(idemp_key)
    if cached:
        return {
            "status": "SUMMARY_ALREADY_EXISTS",
            "summary_id": cached["artifact_id"],
            "pr_number": validated.pr_number,
            "risk_level": validated.risk_level,
            "message": f"A summary for PR #{validated.pr_number} already exists."
        }

    rec = repo.create_pr_summary(
        pr_number=validated.pr_number,
        summary=validated.summary,
        risk_level=validated.risk_level,
        risk_notes=validated.risk_notes,
        source_conversation_id=conversation_id
    )
    repo.record_idempotency(idemp_key, "pr_summary", rec["id"])

    return {
        "status": "RECORD_CREATED",
        "summary_id": rec["id"],
        "pr_number": rec["pr_number"],
        "risk_level": rec["risk_level"],
        "message": f"Persisted structured summary for PR #{rec['pr_number']} (Risk: {rec['risk_level']})."
    }


# --- Tool 7: list_tickets ---
def list_tickets(
    service_id: Optional[str] = None,
    severity: Optional[str] = None,
    include_drafts: bool = True
) -> Dict[str, Any]:
    """List active incidents, historical tickets, and locally created draft tickets."""
    validated = ListTicketsInput(
        service_id=service_id,
        severity=severity,
        include_drafts=include_drafts
    )
    raw_tickets = _load_json_data("tickets.json")
    results = []

    # 1. Process active/historical tickets from dataset
    for t in raw_tickets:
        if validated.service_id and validated.service_id.lower() not in t.get("service_id", "").lower():
            continue
        if validated.severity and validated.severity.upper() != t.get("severity", "").upper():
            continue
        results.append({
            "id": t["id"],
            "title": t["title"],
            "service_id": t["service_id"],
            "severity": t["severity"],
            "status": t["status"],
            "team": t.get("team", "unassigned"),
            "is_draft": False
        })

    # 2. Process locally drafted tickets from SQLite
    if validated.include_drafts:
        local_drafts = repo.list_ticket_drafts()
        for d in local_drafts:
            if validated.service_id and d.get("service_id") and validated.service_id.lower() not in d["service_id"].lower():
                continue
            if validated.severity and validated.severity.upper() != d.get("priority", "").upper():
                continue
            results.append({
                "id": d["id"],
                "title": d["title"],
                "service_id": d.get("service_id"),
                "severity": d["priority"],
                "status": d["status"],
                "team": d["team"],
                "is_draft": True
            })

    return {
        "count": len(results),
        "tickets": results
    }
