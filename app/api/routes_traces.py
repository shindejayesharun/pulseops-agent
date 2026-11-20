from fastapi import APIRouter
from app.db.repository import repo

router = APIRouter(prefix="/api/traces", tags=["Telemetry"])


@router.get("/{conversation_id}")
def get_traces_for_conversation(conversation_id: str):
    traces = repo.get_tool_traces(conversation_id)
    return {
        "conversation_id": conversation_id,
        "count": len(traces),
        "traces": traces
    }
