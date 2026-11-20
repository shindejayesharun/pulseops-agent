import asyncio
import json
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from app.agent.orchestrator import PulseOpsOrchestrator
from app.db.repository import repo

router = APIRouter(prefix="/api", tags=["Chat"])
executor = ThreadPoolExecutor(max_workers=8)


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


@router.post("/chat/stream")
async def chat_stream_endpoint(req: ChatRequest):
    conv_id = req.conversation_id or f"conv_{uuid.uuid4().hex[:12]}"
    loop = asyncio.get_running_loop()
    queue = asyncio.Queue()

    def callback(event_type: str, data: Any):
        loop.call_soon_threadsafe(queue.put_nowait, (event_type, data))

    async def event_generator():
        yield "event: connected\ndata: {\"status\": \"connected\"}\n\n"

        orch = PulseOpsOrchestrator(mode=req.mode, provider_name=req.provider)
        future = loop.run_in_executor(
            executor,
            orch.run_turn,
            conv_id,
            req.message,
            callback
        )

        while not future.done() or not queue.empty():
            try:
                event_type, payload = await asyncio.wait_for(queue.get(), timeout=0.1)
                yield f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"
            except asyncio.TimeoutError:
                continue

        result = await future
        yield f"event: done\ndata: {json.dumps(result)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/conversations")
def list_conversations():
    return {"conversations": repo.list_conversations()}


@router.get("/conversations/{conversation_id}/messages")
def get_conversation_messages(conversation_id: str):
    messages = repo.get_messages(conversation_id)
    return {"conversation_id": conversation_id, "messages": messages}
