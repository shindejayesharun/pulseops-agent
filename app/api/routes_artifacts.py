import json
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter
from app.config import settings
from app.db.repository import repo

router = APIRouter(prefix="/api", tags=["Artifacts & Catalogs"])


def _load_data_file(filename: str) -> List[Dict[str, Any]]:
    path = settings.data_dir / filename
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get("/services")
def list_services():
    """Returns the full service catalog with ownership, SLOs, and dependencies."""
    services = _load_data_file("services.json")
    return {
        "count": len(services),
        "services": services
    }


@router.get("/tickets")
def list_ticket_drafts():
    """Returns local ticket drafts pending human approval."""
    drafts = repo.list_ticket_drafts()
    return {
        "count": len(drafts),
        "tickets": drafts
    }


@router.get("/tickets/all")
def list_all_tickets_and_incidents():
    """Returns combined active incidents from synthetic records and local drafts."""
    raw_tickets = _load_data_file("tickets.json")
    drafts = repo.list_ticket_drafts()
    combined = []

    for t in raw_tickets:
        combined.append({
            "id": t["id"],
            "title": t["title"],
            "service_id": t.get("service_id"),
            "severity": t.get("severity"),
            "status": t.get("status"),
            "team": t.get("team"),
            "is_draft": False,
            "created_at": t.get("created_at")
        })

    for d in drafts:
        combined.append({
            "id": d["id"],
            "title": d["title"],
            "service_id": d.get("service_id"),
            "severity": d.get("priority"),
            "status": d.get("status"),
            "team": d.get("team"),
            "is_draft": True,
            "created_at": d.get("created_at")
        })

    return {
        "count": len(combined),
        "active_incidents_count": len(raw_tickets),
        "drafts_count": len(drafts),
        "tickets": combined
    }


@router.get("/prs")
def list_prs():
    """Returns all pull requests in the Northstar repository."""
    prs = _load_data_file("prs.json")
    return {
        "count": len(prs),
        "prs": prs
    }


@router.get("/prs/summaries")
def list_pr_summaries():
    """Returns generated pull request structured summaries."""
    summaries = repo.list_pr_summaries()
    return {
        "count": len(summaries),
        "summaries": summaries
    }
