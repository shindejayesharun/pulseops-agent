import uuid
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.agent.orchestrator import PulseOpsOrchestrator
from app.db.repository import repo

router = APIRouter(prefix="/api", tags=["Chat"])


class ChatRequest(BaseModel):
    conversation_id: Optional[str] = Field(default=None, description="Conversation session ID")
    message: str = Field(min_length=1, description="User prompt or instruction")
    mode: Optional[str] = Field(default=None, description="Override engine mode: 'mock' or 'live'")
    provider: Optional[str] = Field(default=None, description="Override LLM provider: 'openai' or 'grok'")


class ChatResponse(BaseModel):
    conversation_id: str
    run_id: str
    response: str
    refusal_triggered: bool
    step_count: int
    tool_traces: List[Dict[str, Any]]
    duration_ms: float


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    conv_id = req.conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
    try:
        orch = PulseOpsOrchestrator(mode=req.mode, provider_name=req.provider)
        res = orch.run_turn(conv_id, req.message)
        return ChatResponse(
            conversation_id=res["conversation_id"],
            run_id=res["run_id"],
            response=res["response"],
            refusal_triggered=res["refusal_triggered"],
            step_count=res["step_count"],
            tool_traces=res["tool_traces"],
            duration_ms=res["duration_ms"],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/conversations")
def list_conversations():
    return {"conversations": repo.list_conversations()}


@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: str):
    messages = repo.get_messages(conversation_id)
    return {"conversation_id": conversation_id, "messages": messages}
