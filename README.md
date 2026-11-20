# ⚡ PulseOps Agent
**Autonomous Engineering Operations Assistant for Northstar Checkout**  
*Built for the Robosoft AI Engineer (AI Solutions) Take-Home Assignment*

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.14-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Framework: LangGraph](https://img.shields.io/badge/Orchestrator-LangGraph-orange.svg)](https://github.com/langchain-ai/langgraph)
[![Eval Pass Rate](https://img.shields.io/badge/Evaluations-16%2F16%20Passed%20(100%25)-brightgreen.svg)](evals/results.sample.md)

---

## 1. Overview & Purpose

**PulseOps** is an autonomous, agent-native Engineering Operations Assistant built to streamline production incident triage, service catalog discovery, and pull request analysis. Operating over a realistic synthetic microservices ecosystem (**"Northstar Checkout"**), PulseOps performs multi-step ReAct reasoning to answer technical questions with grounded runbook citations and execute guarded, Human-In-The-Loop (HITL) local draft actions.

### Core Capabilities
* 📖 **Grounded Runbook Triage**: Answers complex operational and architectural queries with verifiable Markdown file citations.
* 🔍 **Service & PR Discovery**: Queries service catalogs, dependency graphs, SLO availability targets, and pull request metadata.
* 📝 **Safe Ticket Drafting (HITL)**: Persists validated incident and bug ticket drafts locally to SQLite with idempotency deduplication (strictly no unauthorized writes to production Jira).
* 🛡️ **Autonomous PR Summarization**: Produces structured change summaries and deployment risk assessments (`LOW`, `MEDIUM`, `HIGH`).
* 🚫 **Deterministic Safety Refusal**: Intercepts out-of-scope external mutations (e.g. social media posts) and destructive operations before tool invocation.
* ⚡ **Dual Engine (Mock vs Live)**: Runs 100% offline via a deterministic mock planner (zero API keys, zero cost) or live via OpenAI (`gpt-4o`) / Grok.

---

## 2. Quickstart & Installation

PulseOps runs with standard Python or via Docker Compose. **Zero API keys are required to test the full application and evaluation suite in mock mode.**

### Option A: Standard Local Setup (Recommended)

1. **Clone & Setup Environment**:
   ```bash
   git clone <repo-url>
   cd pulseops-agent
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure Environment** (Optional for mock mode):
   ```bash
   cp .env.example .env
   # Default LLM_MODE=mock works 100% offline.
   # To use Live LLM: set LLM_MODE=live and provide OPENAI_API_KEY.
   ```

3. **Run Automated Unit Tests**:
   ```bash
   pytest -v
   # 11 passed in < 3s
   ```

4. **Run Golden Benchmark Suite**:
   ```bash
   python evals/run_evals.py --mode mock
   # 16/16 cases passed (100% pass rate)
   ```

5. **Start FastAPI Application & Web UI**:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
   ```
   Open your browser to: **[http://localhost:8000](http://localhost:8000)**  
   Interactive API documentation (Swagger): **[http://localhost:8000/docs](http://localhost:8000/docs)**

---

### Option B: One-Command Docker Bring-Up

```bash
docker compose up --build
```
Access the application at `http://localhost:8000`.

---

## 3. Demo Walkthrough

### 1. Interactive Terminal CLI (`cli/demo.py`)
Run the automated end-to-end canned walkthrough:
```bash
python cli/demo.py --demo
```
This demonstrates:
1. Grounded SLO lookup for `checkout-api`.
2. Runbook triage with exact Markdown citations.
3. Multi-tool chaining: Looks up service owner $\to$ files local P3 ticket draft.
4. Pull request risk analysis and structured summarization.
5. Upstream policy refusal when prompted to post an outage to Twitter/X.

Or launch the interactive terminal chat:
```bash
python cli/demo.py
```

### 2. Modern Web Dashboard
Navigate to `http://localhost:8000` to interact with:
* **Interactive Chat**: Includes quick-prompt suggestion chips and markdown responses.
* **Live Tool Traces Tab**: Real-time telemetry feed displaying step numbers, execution latency (in ms), JSON inputs, and results.
* **Ticket Drafts Tab**: Live cards for created ticket drafts (`DRAFT_PENDING_APPROVAL`, priority badge, assigned team).
* **PR Summaries Tab**: Live cards for summarized pull requests and risk notes.

---

## 4. System Architecture & Component Design

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

## 5. Golden Evaluation Benchmark Results

The evaluation harness evaluates 16 diverse test cases covering single-turn Q&A, service dependencies, multi-tool chains, and safety refusals:

```bash
python evals/run_evals.py --mode mock
```

```text
=== Benchmark Summary ===
Total Cases:     16
Passed:          16
Failed:          0
Pass Rate:       100.0%
Avg Latency:     65.33 ms
p95 Latency:     141.34 ms
```

Detailed results and per-case assertion breakdowns are committed in **[`evals/results.sample.md`](evals/results.sample.md)**.

---

## 6. Project Documentation Directory

* 📘 **[DESIGN.md](DESIGN.md)**: Architecture Decision Records (ADRs), tradeoff analyses (LangGraph vs Custom loop, SQLite FTS5 vs Milvus), and enterprise production scaling strategy.
* 📓 **[PROCESS.md](PROCESS.md)**: Transparent AI-native engineering log detailing decomposition, prompt engineering, verification loops, and what we would automate next.
* 📗 **[ASSUMPTIONS.md](ASSUMPTIONS.md)**: Explicit domain boundaries, safety policies, and technical constraints.
* 📋 **[PLAN.md](PLAN.md)**: Original phased implementation roadmap.

---

## 7. Operational Metadata & Scope Limits

* **Candidate**: AI Engineer (AI Solutions)
* **Total Time Invested**: ~10.5 hours (Design & Evals: 1.5h, Core Tools & Data: 3.5h, Agent & Persistence: 2.5h, UI/CLI: 1.5h, Hardening & Docs: 1.5h).
* **LLM Modes Tested**:
  * `LLM_MODE=mock`: 100% offline, deterministic heuristic state machine ($0.00 API cost).
  * `LLM_MODE=live`: Tested with OpenAI `gpt-4o` (~$0.06 total token expenditure).
* **Scope Limits Respected**:
  * No real external Jira/GitHub writes (local drafts only).
  * No real SSO/IAM (session UUIDs with local auth boundaries).
  * No external vector database required for a 25 KB corpus (clean `BaseRetriever` interface provided).

---

## 8. Submission Checklist Verification

- [x] **Fresh clone verification**: Starts cleanly with `pip install -r requirements.txt && uvicorn app.main:app`.
- [x] **Zero-Key Mock Mode**: Full evaluation suite and UI function seamlessly offline with `LLM_MODE=mock`.
- [x] **Live Mode Support**: Compatible with OpenAI (`gpt-4o`) and Grok.
- [x] **Grounded Answers with Citations**: All RAG answers link directly to source Markdown docs and line ranges.
- [x] **Safe HITL Writes**: Ticket drafts and PR summaries persist locally without mutating external systems.
- [x] **Tool Telemetry**: Full tool traces visible in database, Web UI, and CLI.
- [x] **Golden Eval Suite ($\ge 16$ cases)**: Multi-tool chains and policy refusals thoroughly verified.
- [x] **Single-Command Evals**: `python evals/run_evals.py` outputs benchmark scorecard.
- [x] **Documentation Suite**: Complete `README.md`, `DESIGN.md`, `PROCESS.md`, and `ASSUMPTIONS.md`.
- [x] **Zero Leaked Secrets**: `.env` ignored; `.env.example` provided.
