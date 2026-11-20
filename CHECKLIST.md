# PulseOps Agent — Candidate Submission Checklist (CHECKLIST.md)
**Role:** AI Engineer (AI Solutions) | **Context:** Engineering Ops Autonomous Agent  
**Assignment Brief:** Robosoft AI Take-Home (`pulseops-candidate-brief.pdf`)

---

## Submission Checklist Verification Matrix

| Brief Requirement | Status | Implementation Details / File References |
| :--- | :---: | :--- |
| **Fresh clone / clean env** | ✅ Verified | App starts with single documented commands (`pip install -r requirements.txt && python verify_all.py` or `docker compose up`). |
| **Grounded QA with citations** | ✅ Verified | RAG queries cite exact source paths (e.g. `[data/docs/oncall_runbook_checkout.md]`). Verified in `tests/test_unit.py` and `eval-qa-02`. |
| **Create ticket draft via agent** | ✅ Verified | Creates local validated drafts in SQLite `ticket_drafts` table with `status="DRAFT_PENDING_APPROVAL"`. Zero external Jira writes. |
| **Summarize PR via agent** | ✅ Verified | Creates structured summaries with deployment risk tiers (`LOW`, `MEDIUM`, `HIGH`) and rollback notes in SQLite `pr_summaries`. |
| **Tool traces visible in DB / UI** | ✅ Verified | OpenTelemetry-style traces recorded in `tool_traces` table. Visible in real-time UI trace drawer and CLI telemetry tables. |
| **Golden evaluation suite** | ✅ Verified | **16 golden cases** in `evals/cases.jsonl` (exceeds $\ge 12$ requirement). Single command: `python evals/run_evals.py --mode mock`. |
| **$\ge 1$ Policy / Refusal case** | ✅ Verified | Shipped **2 policy refusal cases** (`eval-refuse-01`, `eval-refuse-02`) blocking external Twitter posts and destructive DB mutations. |
| **$\ge 1$ Multi-tool chain case** | ✅ Verified | Shipped **2 multi-tool chain cases** (`eval-chain-01`, `eval-chain-02`) enforcing sequential tool execution (`get_service` $\to$ `create_ticket_draft`). |
| **Dual Engine (Mock + Live)** | ✅ Verified | Works 100% offline with `LLM_MODE=mock` (0 API keys needed, 16/16 passed). Also supports live OpenAI (`gpt-4o`) and Grok. |
| **FastAPI HTTP REST API** | ✅ Verified | Endpoints: `POST /api/chat`, `POST /api/chat/stream` (SSE), `GET /api/traces/{id}`, `GET /api/tickets`, `GET /api/services`, `GET /api/health`. |
| **Web UI & CLI Interfaces** | ✅ Verified | Embedded sleek Single-Page App at `http://localhost:8000` + animated Rich interactive CLI (`cli/demo.py`). |
| **Local Persistence (SQLite WAL)** | ✅ Verified | Relational schema in SQLite with WAL mode, foreign keys, and idempotency deduplication (`app/db/database.py`). |
| **DESIGN.md (ADR / Tradeoffs)** | ✅ Verified | Complete design note covering LangGraph choice, FTS5 vs Milvus, dual engine, and enterprise PostgreSQL scaling. |
| **PROCESS.md (AI-Native Workflow)**| ✅ Verified | Detailed answers to all 6 brief questions: decomposition, tools used, prompts, verification loop, iteration story, and next automations. |
| **ASSUMPTIONS.md** | ✅ Verified | Explicitly documents domain bounds, synthetic corpus scope, HITL draft safety rules, and environment constraints. |
| **No Leaked Secrets** | ✅ Verified | `.env` ignored in `.gitignore`; clean `.env.example` provided with dummy values. |
| **Hours Logged & Timebox** | ✅ Verified | ~10.5 total hours logged in `README.md`; focused on complete, robust core. |

---

## Benchmark Scorecard Summary

```text
=== Benchmark Summary ===
Total Cases:     16
Passed:          16 (100.0%)
Failed:          0
Avg Latency:     79.45 ms
p95 Latency:     178.49 ms
Committed File:  evals/results.sample.md
```

| Evaluation Category | Test Cases | Pass Rate | Key Verification Focus |
| :--- | :---: | :---: | :--- |
| **Knowledge Q&A Grounding** | 4 | 100% | Cites runbooks, extracts exact SLOs and HTTP headers |
| **Service & Dependency Discovery** | 2 | 100% | Resolves service catalog dependencies and on-call rotations |
| **Pull Request Inspection** | 2 | 100% | Analyzes open PR metadata, diff summaries, and authors |
| **Incident Ticket Drafting (HITL)** | 2 | 100% | Validates Pydantic schema, priority tiers, and idempotency |
| **PR Summarization (Risk Notes)** | 2 | 100% | Evaluates deployment risk rating and failure mode analysis |
| **Multi-Tool Chains** | 2 | 100% | Verifies sequential execution order (e.g. lookup $\to$ write) |
| **Policy Safety Refusal** | 2 | 100% | Guarantees zero writes and polite refusal for disallowed operations |
