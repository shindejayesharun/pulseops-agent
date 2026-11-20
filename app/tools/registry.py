import time
import traceback
from typing import Any, Callable, Dict, List, Optional
from app.db.repository import repo
from app.tools.implementations import (
    create_ticket_draft,
    get_pr,
    get_service,
    list_open_prs,
    search_docs,
    summarize_pr,
)


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "Search internal engineering documentation and on-call runbooks for answers and triage procedures.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Keywords, questions, or topics to search in runbooks and architecture docs"
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Max number of matching documents to return (default: 3)"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_service",
            "description": "Retrieve service inventory metadata, owner team, SLO, on-call rotation, and dependencies.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name_or_id": {
                        "type": "string",
                        "description": "Service ID or name (e.g. 'checkout-api', 'svc-payment-gw', 'fraud-detector')"
                    }
                },
                "required": ["service_name_or_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_open_prs",
            "description": "List open pull requests with authors, file changes, and risk ratings, optionally filtered by service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_id": {
                        "type": "string",
                        "description": "Optional service ID to filter (e.g. 'svc-checkout-api')"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_pr",
            "description": "Fetch detailed metadata, files changed, and diff summary for a specific pull request number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pr_number": {
                        "type": "integer",
                        "description": "Pull request number (e.g. 101, 102, 103)"
                    }
                },
                "required": ["pr_number"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "create_ticket_draft",
            "description": "Create a local incident or defect ticket draft for human approval. Never publishes to external Jira.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Clear title summarizing the issue"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed problem statement, impact, and triage notes"
                    },
                    "priority": {
                        "type": "string",
                        "enum": ["P0", "P1", "P2", "P3", "P4"],
                        "description": "Severity tier"
                    },
                    "team": {
                        "type": "string",
                        "description": "Target team (e.g. 'payments', 'security', 'catalog', 'infrastructure', 'experience')"
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Tags or categories"
                    },
                    "service_id": {
                        "type": "string",
                        "description": "Associated service ID"
                    }
                },
                "required": ["title", "description", "priority", "team"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "summarize_pr",
            "description": "Produce and persist a structured PR summary with risk assessment and rollback notes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pr_number": {
                        "type": "integer",
                        "description": "PR number being summarized"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Summary of business purpose and architectural changes"
                    },
                    "risk_level": {
                        "type": "string",
                        "enum": ["LOW", "MEDIUM", "HIGH"],
                        "description": "Deployment risk tier"
                    },
                    "risk_notes": {
                        "type": "string",
                        "description": "Rollback strategy and potential failure modes"
                    }
                },
                "required": ["pr_number", "summary", "risk_level", "risk_notes"]
            }
        }
    }
]


TOOL_MAPPING: Dict[str, Callable] = {
    "search_docs": search_docs,
    "get_service": get_service,
    "list_open_prs": list_open_prs,
    "get_pr": get_pr,
    "create_ticket_draft": create_ticket_draft,
    "summarize_pr": summarize_pr,
}


def dispatch_tool(
    tool_name: str,
    args: Dict[str, Any],
    conversation_id: Optional[str] = None,
    step_number: int = 1,
    run_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes a registered tool within a safety boundary, measures execution latency,
    and persists an OpenTelemetry-style telemetry trace to SQLite.
    """
    if tool_name not in TOOL_MAPPING:
        err_msg = f"Security Error: Tool '{tool_name}' is not in the authorized tool allowlist."
        if conversation_id:
            repo.record_tool_trace(
                conversation_id=conversation_id,
                step_number=step_number,
                tool_name=tool_name,
                args_json=args,
                result_json={"error": err_msg},
                ok=False,
                latency_ms=0.0,
                run_id=run_id
            )
        return {"error": err_msg, "ok": False}

    func = TOOL_MAPPING[tool_name]
    start_time = time.perf_counter()
    ok = True
    result: Any = None

    try:
        # Pass conversation_id to write tools for lineage tracking
        if tool_name in ("create_ticket_draft", "summarize_pr"):
            args_with_ctx = dict(args)
            if "conversation_id" not in args_with_ctx:
                args_with_ctx["conversation_id"] = conversation_id
            result = func(**args_with_ctx)
        else:
            result = func(**args)
    except Exception as e:
        ok = False
        result = {
            "error": str(e),
            "traceback": traceback.format_exc()
        }

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    if conversation_id:
        repo.record_tool_trace(
            conversation_id=conversation_id,
            step_number=step_number,
            tool_name=tool_name,
            args_json=args,
            result_json=result,
            ok=ok,
            latency_ms=duration_ms,
            run_id=run_id
        )

    return {
        "ok": ok,
        "tool_name": tool_name,
        "args_json": args,
        "result": result,
        "latency_ms": duration_ms
    }
