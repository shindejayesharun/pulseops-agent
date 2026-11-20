import time
import uuid
from typing import Any, Dict, List, Optional
from langgraph.graph import END, StateGraph
from app.agent.guardrails import check_policy_violations
from app.agent.prompts import SYSTEM_PROMPT
from app.agent.providers import get_llm_provider
from app.agent.state import AgentState
from app.config import settings
from app.db.repository import repo
from app.tools.registry import TOOL_DEFINITIONS, dispatch_tool


class PulseOpsOrchestrator:
    def __init__(self, mode: Optional[str] = None, provider_name: Optional[str] = None):
        self.mode = mode or settings.llm_mode
        self.provider_name = provider_name or settings.llm_provider
        self.provider = get_llm_provider(mode=self.mode, provider=self.provider_name)
        self.workflow = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(AgentState)

        # 1. Add Nodes
        graph.add_node("policy_guard", self._policy_guard_node)
        graph.add_node("reasoning", self._reasoning_node)
        graph.add_node("tool_execution", self._tool_execution_node)

        # 2. Set Entrypoint
        graph.set_entry_point("policy_guard")

        # 3. Add Edges & Conditional Transitions
        graph.add_conditional_edges(
            "policy_guard",
            self._route_after_guard,
            {
                "blocked": END,
                "allowed": "reasoning"
            }
        )

        graph.add_conditional_edges(
            "reasoning",
            self._route_after_reasoning,
            {
                "execute_tools": "tool_execution",
                "done": END
            }
        )

        graph.add_edge("tool_execution", "reasoning")

        return graph.compile()

    # --- Node Handlers ---
    def _policy_guard_node(self, state: AgentState) -> AgentState:
        # Check latest user message
        user_prompt = ""
        for m in reversed(state.get("messages", [])):
            if m.get("role") == "user":
                user_prompt = m.get("content", "")
                break

        is_violation, explanation = check_policy_violations(user_prompt)
        if is_violation and explanation:
            state["refusal_triggered"] = True
            state["final_answer"] = explanation
            # Save refusal assistant message
            repo.add_message(state["conversation_id"], "assistant", explanation)
            state["messages"].append({
                "role": "assistant",
                "content": explanation
            })
        return state

    def _reasoning_node(self, state: AgentState) -> AgentState:
        if state.get("refusal_triggered"):
            return state

        # Check recursion / step limit guard
        if state.get("step_count", 0) >= settings.max_tool_rounds:
            halt_msg = f"Controlled Stop: Reached maximum execution rounds ({settings.max_tool_rounds}). Halting to prevent infinite loops."
            state["final_answer"] = halt_msg
            repo.add_message(state["conversation_id"], "assistant", halt_msg)
            state["messages"].append({"role": "assistant", "content": halt_msg})
            return state

        plan = self.provider.plan_next_step(state["messages"], TOOL_DEFINITIONS)

        if plan.get("type") == "tool_calls":
            state["pending_tool_calls"] = plan.get("tool_calls", [])
            # Append assistant message with tool calls
            state["messages"].append({
                "role": "assistant",
                "content": None,
                "tool_calls": plan.get("tool_calls")
            })
        else:
            answer = plan.get("content", "")
            state["final_answer"] = answer
            state["pending_tool_calls"] = []
            repo.add_message(state["conversation_id"], "assistant", answer)
            state["messages"].append({
                "role": "assistant",
                "content": answer
            })

        return state

    def _tool_execution_node(self, state: AgentState) -> AgentState:
        pending = state.get("pending_tool_calls", [])
        conv_id = state.get("conversation_id")
        run_id = state.get("run_id")
        step_num = state.get("step_count", 0) + 1

        for call in pending:
            tool_name = call["name"]
            tool_args = call.get("args", {})
            call_id = call.get("id", f"call_{uuid.uuid4().hex[:8]}")

            exec_res = dispatch_tool(
                tool_name=tool_name,
                args=tool_args,
                conversation_id=conv_id,
                step_number=step_num,
                run_id=run_id
            )

            state["tool_traces"].append(exec_res)

            # Append tool result to conversation history
            state["messages"].append({
                "role": "tool",
                "name": tool_name,
                "tool_call_id": call_id,
                "content": exec_res["result"]
            })

        state["step_count"] = step_num
        state["pending_tool_calls"] = []
        return state

    # --- Router Helpers ---
    def _route_after_guard(self, state: AgentState) -> str:
        if state.get("refusal_triggered"):
            return "blocked"
        return "allowed"

    def _route_after_reasoning(self, state: AgentState) -> str:
        if state.get("final_answer") is not None:
            return "done"
        if state.get("pending_tool_calls"):
            return "execute_tools"
        return "done"

    # --- Primary Entrypoint ---
    def run_turn(self, conversation_id: str, user_input: str) -> Dict[str, Any]:
        start_time = time.perf_counter()
        run_id = f"run_{uuid.uuid4().hex[:10]}"

        # 1. Ensure conversation exists in DB
        conv = repo.get_conversation(conversation_id)
        if not conv:
            repo.create_conversation(conversation_id=conversation_id, user_label=f"Chat {conversation_id[:8]}")

        # 2. Start Agent Run Audit Record
        run_id = f"run_{uuid.uuid4().hex[:10]}"
        repo.record_agent_run(
            conversation_id=conversation_id,
            provider=f"{self.mode}:{self.provider_name}",
            model=getattr(self.provider, "model", "mock-planner"),
            status="running",
            run_id=run_id
        )

        # 3. Persist User Message
        repo.add_message(conversation_id, "user", user_input)

        # 4. Load past message history
        db_messages = repo.get_messages(conversation_id)
        history = [{"role": m["role"], "content": m["content"]} for m in db_messages]

        # 5. Construct initial state
        initial_state: AgentState = {
            "conversation_id": conversation_id,
            "run_id": run_id,
            "messages": history,
            "step_count": 0,
            "pending_tool_calls": [],
            "tool_traces": [],
            "final_answer": None,
            "refusal_triggered": False,
            "error": None
        }

        # 6. Invoke LangGraph
        result_state = self.workflow.invoke(initial_state)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

        # 7. Finalize Agent Run Audit in DB
        status = "refused" if result_state.get("refusal_triggered") else "completed"
        repo.update_agent_run(
            run_id=run_id,
            status=status,
            duration_ms=duration_ms
        )

        return {
            "conversation_id": conversation_id,
            "run_id": run_id,
            "response": result_state.get("final_answer", ""),
            "refusal_triggered": result_state.get("refusal_triggered", False),
            "step_count": result_state.get("step_count", 0),
            "tool_traces": result_state.get("tool_traces", []),
            "duration_ms": duration_ms
        }
