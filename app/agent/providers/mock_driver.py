import re
import uuid
from typing import Any, Dict, List
from app.agent.providers.base import BaseLLMProvider


class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic rule-based state machine planner.
    Enables 100% offline, reproducible testing and evaluation with zero external API dependencies.
    """

    def plan_next_step(
        self,
        messages: List[Dict[str, Any]],
        tool_definitions: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        # Extract initial user query
        user_query = ""
        for m in messages:
            if m.get("role") == "user":
                user_query = m.get("content", "")

        q_lower = user_query.lower()

        # Collect executed tool names from history
        executed_tools = []
        last_tool_name = None
        last_tool_result = None

        for m in messages:
            if m.get("role") == "tool":
                tname = m.get("name")
                if tname:
                    executed_tools.append(tname)
                    last_tool_name = tname
                    last_tool_result = m.get("content")

        # -------------------------------------------------------------
        # 1. Multi-Tool Chain Cases
        # -------------------------------------------------------------
        # Chain 1: Service Lookup -> Ticket Draft
        if "who owns checkout-api" in q_lower and ("p3 ticket" in q_lower or "ticket draft" in q_lower):
            if "get_service" not in executed_tools:
                return self._call_tool("get_service", {"service_name_or_id": "checkout-api"})
            elif "create_ticket_draft" not in executed_tools:
                return self._call_tool("create_ticket_draft", {
                    "title": "Missing runbook documentation for checkout-api",
                    "description": "On-call engineers noted missing runbook section for checkout-api failure modes. Ownership belongs to the payments team.",
                    "priority": "P3",
                    "team": "payments",
                    "service_id": "svc-checkout-api",
                    "labels": ["runbook", "documentation", "triage"]
                })
            else:
                return self._final_answer(
                    "The `checkout-api` service is owned by the **payments** team (on-call: `@payments-oncall`, Slack: `#payments-team`).\n\n"
                    "As requested, I have created a **P3** local ticket draft for the missing runbook section.\n"
                    "Status: **DRAFT_PENDING_APPROVAL** (persisted locally in SQLite for human review)."
                )

        # Chain 2: PR #103 -> Service Lookup -> Summarize PR
        if "103" in q_lower and "dependencies" in q_lower and "summarize" in q_lower:
            if "get_pr" not in executed_tools:
                return self._call_tool("get_pr", {"pr_number": 103})
            elif "get_service" not in executed_tools:
                return self._call_tool("get_service", {"service_name_or_id": "fraud-detector"})
            elif "summarize_pr" not in executed_tools:
                return self._call_tool("summarize_pr", {
                    "pr_number": 103,
                    "summary": "Caches external threat intelligence IP risk scores in Redis with a 5-minute TTL to reduce p99 scoring latency.",
                    "risk_level": "LOW",
                    "risk_notes": "Low risk optimization. Dependent on Redis connectivity; falls back to live evaluation if cache is unavailable."
                })
            else:
                return self._final_answer(
                    "I inspected PR #103 and the `fraud-detector` dependencies (`svc-ledger`).\n\n"
                    "**PR Summary**: Adds Redis IP reputation caching with a 5-minute TTL by `@marcus_sec`. Touches 4 files.\n"
                    "**Risk Tier**: **LOW** (Deployment risk is low; cache miss falls back cleanly).\n"
                    "A structured summary record has been persisted locally."
                )

        # -------------------------------------------------------------
        # 2. PR Summarization Actions (get_pr -> summarize_pr)
        # -------------------------------------------------------------
        if "summarize pr" in q_lower or ("summarize" in q_lower and "pr" in q_lower):
            pr_num = 101 if "101" in q_lower else (103 if "103" in q_lower else 102)
            if "get_pr" not in executed_tools:
                return self._call_tool("get_pr", {"pr_number": pr_num})
            elif "summarize_pr" not in executed_tools:
                risk = "MEDIUM" if pr_num == 101 else "LOW"
                return self._call_tool("summarize_pr", {
                    "pr_number": pr_num,
                    "summary": f"Pull Request #{pr_num} architectural changes and resilience hardening.",
                    "risk_level": risk,
                    "risk_notes": "Requires monitoring of circuit breaker telemetry and canary deployment."
                })
            else:
                risk = "MEDIUM" if pr_num == 101 else "LOW"
                return self._final_answer(
                    f"Successfully generated and persisted structured summary for PR #{pr_num}.\n"
                    f"- **Risk Level**: {risk}\n"
                    f"- **Notes**: Circuit breaker protections require canary verification.\n"
                    f"- **Status**: Persisted to local records for engineering review."
                )

        # -------------------------------------------------------------
        # 3. Ticket Draft Creation Actions
        # -------------------------------------------------------------
        if "ticket" in q_lower and ("create" in q_lower or "open" in q_lower or "draft" in q_lower):
            if "create_ticket_draft" not in executed_tools:
                priority = "P1" if "p1" in q_lower else ("P2" if "p2" in q_lower else "P3")
                service_id = "svc-checkout-api" if "checkout" in q_lower else "svc-payment-gw"
                team = "payments"
                title = "Elevated latency on payment-gateway affecting checkout" if "latency" in q_lower else "500 error spike on checkout-api during flash sale"
                return self._call_tool("create_ticket_draft", {
                    "title": title,
                    "description": f"Operational incident reported: {user_query}. Automatic local draft created for human triage.",
                    "priority": priority,
                    "team": team,
                    "service_id": service_id,
                    "labels": ["incident", "on-call", priority.lower()]
                })
            else:
                return self._final_answer(
                    f"I have created a local ticket draft in SQLite based on your prompt.\n"
                    f"- **Priority**: {'P1' if 'p1' in q_lower else 'P2'}\n"
                    f"- **Team**: `payments`\n"
                    f"- **HITL Policy**: Created with status `DRAFT_PENDING_APPROVAL`. No live external writes made."
                )

        # -------------------------------------------------------------
        # 4. PR Queries
        # -------------------------------------------------------------
        if "active incident" in q_lower or "list ticket" in q_lower or "existing ticket" in q_lower:
            if "list_tickets" not in executed_tools:
                return self._call_tool("list_tickets", {})
            else:
                return self._final_answer(
                    "Here are the active incidents and tickets in Northstar Checkout:\n"
                    "- **INC-201** (P1): Elevated latency on checkout-api during promotional flash sale (investigating)\n"
                    "- **INC-202** (P2): fraud-detector timeout triggering false positive decline spikes (resolved)\n"
                    "- **TICK-301** (P3): Missing runbook documentation for pricing-engine cache invalidation (open)"
                )

        if "open pr" in q_lower or "list" in q_lower and "pr" in q_lower:
            if "list_open_prs" not in executed_tools:
                return self._call_tool("list_open_prs", {})
            else:
                return self._final_answer(
                    "Here are the currently open Pull Requests in Northstar Checkout:\n"
                    "- **PR #101**: `feat(checkout): Add circuit breaker for payment-gateway calls` by `@alex_dev` (Risk: MEDIUM)\n"
                    "- **PR #102**: `fix(pricing): Fix currency conversion rounding error on discounts` by `@sarah_cat` (Risk: LOW)\n"
                    "- **PR #103**: `perf(fraud): Cache IP reputation scores in Redis with 5m TTL` by `@marcus_sec` (Risk: LOW)"
                )

        if "what changed in pr" in q_lower or "pr #101" in q_lower or "pr 101" in q_lower:
            if "get_pr" not in executed_tools:
                return self._call_tool("get_pr", {"pr_number": 101})
            else:
                return self._final_answer(
                    "In **PR #101** (`feat(checkout): Add circuit breaker for payment-gateway calls`), author `@alex_dev` introduced:\n"
                    "- Exponential backoff and circuit breaker wrapper around `payment-gateway` requests.\n"
                    "- Modified files: `src/clients/payment_client.py`, `src/circuit_breaker.py`, `tests/test_circuit_breaker.py`.\n"
                    "- Diff: +142 lines, -18 lines. Risk: MEDIUM."
                )

        # -------------------------------------------------------------
        # 5. Service Queries
        # -------------------------------------------------------------
        if "slo" in q_lower and "checkout" in q_lower:
            if "get_service" not in executed_tools:
                return self._call_tool("get_service", {"service_name_or_id": "checkout-api"})
            else:
                return self._final_answer(
                    "According to the Northstar service catalog (`data/services.json`), the availability SLO for **checkout-api** (`svc-checkout-api`) is **99.95%**.\n"
                    "- **Owner Team**: `payments`\n"
                    "- **On-Call Handle**: `@payments-oncall`\n"
                    "- **Repo**: `northstar/checkout-api`"
                )

        if "fraud-detector" in q_lower and ("owns" in q_lower or "team" in q_lower or "on call" in q_lower):
            if "get_service" not in executed_tools:
                return self._call_tool("get_service", {"service_name_or_id": "fraud-detector"})
            else:
                return self._final_answer(
                    "The **fraud-detector** service (`svc-fraud`) is owned by the **security** team.\n"
                    "- **On-Call Handle**: `@secops-oncall`\n"
                    "- **SLO**: 99.90% availability\n"
                    "- **Repo**: `northstar/fraud-detector`"
                )

        if "depend" in q_lower and "checkout" in q_lower:
            if "get_service" not in executed_tools:
                return self._call_tool("get_service", {"service_name_or_id": "checkout-api"})
            else:
                return self._final_answer(
                    "The **checkout-api** service directly depends on the following upstream internal microservices:\n"
                    "1. `svc-payment-gw` (`payment-gateway`)\n"
                    "2. `svc-pricing` (`pricing-engine`)\n"
                    "3. `svc-fraud` (`fraud-detector`)"
                )

        # -------------------------------------------------------------
        # 6. Documentation / RAG Queries
        # -------------------------------------------------------------
        if "latency spikes" in q_lower or "runbook" in q_lower:
            if "search_docs" not in executed_tools:
                return self._call_tool("search_docs", {"query": "checkout-api latency spikes triage circuit breaker"})
            else:
                return self._final_answer(
                    "According to the on-call runbook (`[data/docs/oncall_runbook_checkout.md]`):\n\n"
                    "1. **Initial Triage**: Verify service health check (`/checkout/health`) and inspect upstream dependencies (`payment-gateway` and `fraud-detector`).\n"
                    "2. **Circuit Breaker**: If `payment-gateway` latency exceeds 3000ms, ensure the circuit breaker has tripped to OPEN. A manual fail-open can be triggered via `/checkout/admin/circuit-breaker/payment-gw/trip`.\n"
                    "3. **Escalation**: If `ledger-db` is saturated, escalate to `@infra-oncall`."
                )

        if "escalation" in q_lower or "mtta" in q_lower or "p0" in q_lower:
            if "search_docs" not in executed_tools:
                return self._call_tool("search_docs", {"query": "incident escalation target MTTA P0"})
            else:
                return self._final_answer(
                    "According to the Northstar Incident Response Guide (`[data/docs/incident_response_guide.md]`):\n\n"
                    "- **Target MTTA**: Less than **5 minutes** for **P0** critical outages.\n"
                    "- **Target MTTR**: Under 1 hour.\n"
                    "- **Escalation Protocol**: The on-call engineer for the affected service automatically assumes Incident Commander (IC) and spins up `#inc-<date>-<brief-slug>`."
                )

        if "idempotency" in q_lower or "header" in q_lower:
            if "search_docs" not in executed_tools:
                return self._call_tool("search_docs", {"query": "payment idempotency header api spec"})
            else:
                return self._final_answer(
                    "According to the Payment Gateway API Specification (`[data/docs/api_spec_payments.md]`):\n\n"
                    "The mandatory HTTP header for payment idempotency is:\n"
                    "```http\nX-Idempotency-Key: <UUIDv4>\n```\n"
                    "It has a 24-hour TTL in Redis to prevent duplicate credit card authorizations on network retries."
                )

        # Fallback default doc search
        if "search_docs" not in executed_tools:
            return self._call_tool("search_docs", {"query": user_query})
        else:
            return self._final_answer(
                f"I processed your query based on the Northstar internal knowledge base. "
                f"Refer to `data/docs/architecture_overview.md` for architectural context."
            )

    def _call_tool(self, name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "type": "tool_calls",
            "tool_calls": [
                {
                    "id": f"call_{uuid.uuid4().hex[:8]}",
                    "name": name,
                    "args": args
                }
            ]
        }

    def _final_answer(self, text: str) -> Dict[str, Any]:
        return {
            "type": "final_answer",
            "content": text
        }
