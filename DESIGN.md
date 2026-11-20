# PulseOps Agent: Architecture Decision Record & System Design (DESIGN.md)
**Role:** AI Engineer (AI Solutions) | **Domain:** Engineering Ops Autonomous Agent  
**Candidate Evaluation Brief:** Robosoft AI Engineering Take-Home

---

## 1. Context & Problem Statement

Modern software engineering organizations manage dozens of microservices, each accompanied by on-call runbooks, architecture decision records (ADRs), pull requests, and incident tracking tickets. When production incidents occur or engineers need operational clarity, manual triage across fragmented wikis and repositories introduces cognitive fatigue and prolongs Mean Time to Acknowledge (MTTA).

**PulseOps** is designed as a small, agent-native Engineering Operations Assistant for the synthetic e-commerce domain **"Northstar Checkout"**. It answers operational questions from internal Markdown runbooks, inspects service catalogs and open pull requests, and performs guarded, Human-In-The-Loop (HITL) write actions (ticket drafting and PR summarization).

---

## 2. Core Architecture & System Topology

PulseOps follows a **Clean / Hexagonal Architecture** separating core domain logic (agent loop, tool registry, safety rules) from infrastructure adapters (FastAPI, SQLite, LLM SDKs, CLI).

```
+-----------------------------------------------------------------------------------+
|                                  Presentation Layer                               |
|        Modern Single-Page App (SPA)          |         Rich Terminal CLI          |
|    (Chat + Live Traces + Artifact Cards)     |    (Animated Walkthrough + REPL)   |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                           FastAPI HTTP Gateway & Routing                          |
|    POST /api/chat   |   GET /api/traces   |   GET /api/tickets   |   GET /health    |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+-----------------------------------------------------------------------------------+
|                        PulseOps Core Orchestrator (LangGraph)                     |
|  [Policy Guard] ---> [Reasoning Node] <---> [Tool Execution] ---> [Persist Trace] |
|   (Regex Gate)       (ReAct Decisions)     (Pydantic Dispatch)   (Telemetry DB)   |
+---------------------+---------------------------------------+---------------------+
                      |                                       |
                      v                                       v
+-----------------------------------------+   +-------------------------------------+
|        Pluggable LLM Drivers            |   |         Tool Execution Layer        |
|  - Live: OpenAI (`gpt-4o`) / Grok       |   |  - search_docs (SQLite FTS5 / BM25) |
|  - Mock: Deterministic State Machine    |   |  - get_service (Catalog Graph)      |
|    (100% Offline CI & Eval Support)     |   |  - list_open_prs / get_pr           |
+-----------------------------------------+   |  - create_ticket_draft (HITL Safe)  |
                                              |  - summarize_pr (Risk Classifier)   |
                                              +------------------+------------------+
                                                                 |
                                                                 v
+-----------------------------------------------------------------------------------+
|                          Storage & Persistence (SQLite WAL)                       |
|   conversations  |  messages  |  agent_runs  |  tool_traces  |  drafts  |  idemp  |
+-----------------------------------------------------------------------------------+
```

---

## 3. Key Architecture Decisions & Tradeoff Analysis

### ADR 1: LangGraph State Machine vs. Custom Python Loop vs. Multi-Agent Swarm

* **Options Considered**:
  1. *Ad-hoc `while` loop*: Lightweight, zero framework overhead, but difficult to audit, lack of explicit state transitions, and fragile error boundary handling.
  2. *Multi-agent swarm (e.g., separate Retriever Agent + Drafter Agent)*: Increases latency, inflates token cost, introduces unpredictable conversational handoffs, and violates the take-home timebox.
  3. *Single-agent LangGraph `StateGraph` (Chosen)*: Provides explicit state encapsulation (`AgentState`), bounded recursion limits (`max_tool_rounds=6`), clean conditional routing, and deterministic graph validation.
* **Decision**: Adopted a single LangGraph agent with specialized tools. It demonstrates genuine agentic ReAct behavior without the fragility and overhead of premature multi-agent architectures.

### ADR 2: SQLite FTS5 / BM25 vs. Milvus / Vector Database Retrieval

* **Options Considered**:
  1. *Dedicated Vector DB (Milvus / Qdrant)*: Embeddings + hybrid dense/sparse vector search.
  2. *SQLite FTS5 Full-Text Search with BM25 (Chosen)*: In-database full-text search with tokenized Porter stemming.
* **Tradeoff Analysis**:
  - The synthetic knowledge corpus contains 8 documents (~25 KB).
  - Deploying a Milvus cluster or spinning up local embedding models adds 500+ MB of dependencies, heavy CPU/GPU overhead, and non-deterministic cosine distance variance.
  - SQLite FTS5 yields sub-millisecond retrieval, exact keyword matching for code symbols and error codes (e.g. `X-Idempotency-Key`, `Checkout5xxErrorRateSpike`), and zero external infrastructure requirements.
* **Extensibility Strategy**: We defined an abstract `BaseRetriever` interface. If the corpus expands to tens of thousands of unstructured documents requiring semantic synonyms, a `MilvusRetriever` can be swapped in without modifying any agent tools.

### ADR 3: Deterministic Dual-Engine Execution (`Mock` vs. `Live`)

* **Problem**: Reviewers often evaluate take-homes in restricted environments without API keys or with strict spending quotas. Live LLM calls can also introduce subtle test flakiness.
* **Decision**: We engineered a complete **Deterministic Mock Planner (`MockLLMProvider`)**:
  - Implements the exact same `BaseLLMProvider` contract as `OpenAILLMProvider`.
  - Driven by a deterministic state machine that mirrors the ReAct loop, resolving all 16 golden evaluation cases with 100% precision.
  - Allows instant local execution, clean Docker bring-up, and continuous integration (CI) test execution at zero cost.

### ADR 4: Human-In-The-Loop (HITL) Safety & Idempotent Write Actions

* **Safety Principle**: Autonomous agents should **never** directly mutate external production systems without explicit human confirmation.
* **Implementation**:
  - Write tools (`create_ticket_draft`, `summarize_pr`) generate local draft artifacts in SQLite with status `DRAFT_PENDING_APPROVAL`.
  - An `idempotency_records` table prevents duplicate writes if an agent replays a tool call or the user retries a prompt.
  - An upstream **Policy Guard** intercepts prohibited commands (e.g. public Twitter/X broadcasts, destructive table drops) and terminates execution safely before any tools are called.

---

## 4. Production Readiness & Enterprise Scaling Strategy

While SQLite satisfies the take-home's zero-dependency mandate, the architecture is designed for enterprise transition:

| Dimension | Take-Home Implementation | Enterprise Production Target |
| :--- | :--- | :--- |
| **Persistence** | SQLite with Write-Ahead Logging (WAL) | Managed PostgreSQL (AWS Aurora / Cloud SQL) with connection pooling (PgBouncer). |
| **Authentication** | Local sessions with UUID conversation tokens | Enterprise SSO (OIDC / OAuth 2.0 / Entra ID) with JWT verification and RBAC. |
| **Observability** | Local SQLite `tool_traces` table | OpenTelemetry instrumentation exporting spans to Jaeger, Datadog, or Grafana Tempo. |
| **Retrieval** | SQLite FTS5 BM25 search | Hybrid Milvus vector search + cross-encoder reranking for semantic query expansion. |
| **Rate Limiting** | Bounded step count (`max_steps=6`) | Redis-backed sliding window token bucket rate limiter per user/team. |

---

## 5. Evaluation Plan & Quality Metrics

Rather than relying on vague visual inspections, PulseOps employs **Evaluation-Driven Development (EDD)**:

1. **Tool Routing Precision & Recall**: Verifies that the agent calls the exact tools expected for the user prompt.
2. **Trajectory Ordering (Multi-Tool Chains)**: Ensures dependency prerequisites (e.g. `get_service` before `create_ticket_draft`) are strictly respected.
3. **Pydantic Schema Validation**: Ensures all generated draft artifacts conform to strict data types and valid categorical values (`P0`–`P4`, `payments`, `security`).
4. **Refusal Compliance**: Confirms that adversarial or out-of-scope prompts trigger a polite, policy-grounded decline without invoking write tools.
5. **Groundedness & Citations**: Ensures responses cite verifiable internal documentation paths (`[data/docs/...]`).
