from fastapi import APIRouter
from app.db.repository import repo

router = APIRouter(prefix="/api", tags=["Artifacts"])


@router.get("/tickets")
def list_ticket_drafts():
    drafts = repo.list_ticket_drafts()
    return {
        "count": len(drafts),
        "tickets": drafts
    }


@router.get("/prs/summaries")
def list_pr_summaries():
    summaries = repo.list_pr_summaries()
    return {
        "count": len(summaries),
        "summaries": summaries
    }
