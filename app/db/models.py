from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class Conversation(BaseModel):
    id: str
    user_label: Optional[str] = None
    created_at: str
    updated_at: str


class Message(BaseModel):
    id: str
    conversation_id: str
    role: Literal["user", "assistant", "system", "tool"]
    content: str
    created_at: str


class AgentRun(BaseModel):
    id: str
    conversation_id: str
    provider: str
    model: str
    status: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    duration_ms: float = 0.0
    created_at: str


class ToolTrace(BaseModel):
    id: str
    conversation_id: str
    run_id: Optional[str] = None
    step_number: int
    tool_name: str
    args_json: Dict[str, Any]
    result_json: Any
    ok: bool = True
    latency_ms: float = 0.0
    created_at: str


class TicketDraft(BaseModel):
    id: str
    source_conversation_id: Optional[str] = None
    service_id: Optional[str] = None
    title: str
    description: str
    priority: Literal["P0", "P1", "P2", "P3", "P4"]
    team: str
    labels: List[str] = Field(default_factory=list)
    status: str = "DRAFT_PENDING_APPROVAL"
    created_at: str


class PRSummary(BaseModel):
    id: str
    source_conversation_id: Optional[str] = None
    pr_number: int
    summary: str
    risk_level: Literal["LOW", "MEDIUM", "HIGH"]
    risk_notes: str
    created_at: str


class IdempotencyRecord(BaseModel):
    key: str
    action_type: str
    artifact_id: str
    created_at: str
