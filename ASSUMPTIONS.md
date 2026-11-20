# ASSUMPTIONS & DESIGN CONSTRAINTS
**PulseOps Agent — Engineering Ops Autonomous Assistant**

This document outlines the core operational assumptions, scope boundaries, and safety constraints established for the PulseOps prototype, adhering to the requirements of the Robosoft Take-Home Brief.

---

## 1. Domain & Synthetic Knowledge Base
- **Synthetic Domain**: All corporate assets, services, documentation, pull requests, and incident tickets represent a fictional e-commerce checkout ecosystem: **"Northstar Checkout"**.
- **No Proprietary Data**: No real client, employer, or proprietary Robosoft data is used or simulated.
- **Corpus Sizing**: The documentation corpus is intentionally bounded to 8 markdown documents, 6 microservices, 4 pull requests, and 4 sample tickets. This satisfies the requirement that a human engineer can review the complete dataset in under an hour.
- **Corpus Immutability**: The base Markdown documents and service definitions in `data/` are read-only at runtime; dynamic mutations are restricted to SQLite persistence (`ticket_drafts`, `pr_summaries`, `tool_traces`).

---

## 2. Agent Safety & Human-In-The-Loop (HITL) Boundary
- **Zero External Mutations**: The agent does not integrate with live GitHub, production Jira, Slack workspaces, or external cloud infrastructure.
- **Draft-Only Policy**: Any write-side action performed by the agent (`create_ticket_draft`, `summarize_pr`) creates a local, uncommitted draft record in SQLite marked with status `DRAFT_PENDING_APPROVAL`. No live issues or PR approvals are dispatched without human confirmation.
- **Strict Out-of-Scope Refusal**: Any user request attempting to mutate production data, delete infrastructure, or publish external announcements (e.g., tweeting outages) is intercepted and politely declined by the policy guardrail without triggering mutation tools.
- **Bounded Tool Trajectory**: The agent execution loop is strictly bounded by `MAX_TOOL_ROUNDS=6` to eliminate the risk of infinite autonomous tool loops.

---

## 3. Dual Engine & LLM Execution Model
- **Live Mode (`LLM_MODE=live`)**:
  - Primary provider: OpenAI (`gpt-4o` / `gpt-4o-mini`) using the official OpenAI SDK.
  - Secondary provider: Grok / xAI (`grok-beta`) supported through the OpenAI-compatible client interface.
  - Native function calling and structured outputs are utilized for tool routing.
- **Mock Mode (`LLM_MODE=mock`)**:
  - Implements a deterministic, rule-based state machine planner that accurately resolves all golden evaluation cases offline.
  - Guarantees 100% reproducible test and eval runs with zero API key dependencies and zero latency/cost overhead.
- **Failover Strategy**: Cross-provider fallback is restricted to read-only operations to guarantee that partial write failures never create duplicate draft records.

---

## 4. Retrieval & Search Strategy
- **SQLite FTS5 / BM25 Default**: Given the synthetic corpus size (8 files, ~25 KB), SQLite full-text search with BM25 ranking provides deterministic, explainable, sub-millisecond retrieval with exact line citations.
- **Vector DB Justification**: A dedicated vector database (such as Milvus or Qdrant) introduces unneeded operational and computational overhead for a 10-document corpus. However, a clean `BaseRetriever` abstraction is implemented so that semantic vector search can be enabled without modifying tool signatures.

---

## 5. Persistence & Multi-Tenancy
- **SQLite WAL**: SQLite running with `PRAGMA journal_mode=WAL;` and foreign keys enabled serves as the runnable local storage engine.
- **PostgreSQL Ready**: Entity schemas (`conversations`, `messages`, `agent_runs`, `tool_traces`, `ticket_drafts`, `pr_summaries`, `idempotency_records`) are modeled cleanly in SQLAlchemy to ensure seamless migration to PostgreSQL for multi-tenant production deployments.
- **Idempotency**: Repeated write requests with identical parameters or idempotency keys return existing artifact records rather than creating duplicate entries.
