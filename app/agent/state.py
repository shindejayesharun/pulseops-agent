from typing import Any, Dict, List, Optional, TypedDict


class AgentState(TypedDict):
    """LangGraph State representation for PulseOps Agent turns."""
    conversation_id: str
    run_id: str
    messages: List[Dict[str, Any]]
    step_count: int
    pending_tool_calls: List[Dict[str, Any]]
    tool_traces: List[Dict[str, Any]]
    final_answer: Optional[str]
    refusal_triggered: bool
    error: Optional[str]
