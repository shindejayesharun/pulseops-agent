PulseOps Agent — Production-Grade Architecture & Implementation Plan
We'll build your Robosoft AI Engineer take-home assignment using production-grade engineering practices, while respecting the assignment's scope and time limit.

Since you have OpenAI and Grok API keys, we can implement a real LLM-powered agent with provider abstraction, persistent conversations, multi-step tool execution, retrieval, structured actions, evaluation, observability, and security controls.

The objective is not just to make a chatbot work. It is to demonstrate that you can design, implement, test, and explain a reliable AI agent system end to end.
1. Architecture decisions
Backend

FastAPI + Pydantic v2


Agent

LangGraph


LLM

OpenAI / Grok / Mock


Persistence

SQLite, PostgreSQL-ready


Retrieval

BM25 / FTS5 first


Frontend

React or lightweight HTML


Testing

Pytest + golden evaluations


Observability

Structured logs + tool traces




Key technical decisions
Component	Decision	Reason
Agent orchestration	LangGraph	Explicit state, bounded execution, extensibility
Primary LLM	OpenAI	Use your existing API key
Secondary LLM	Grok	Configurable alternative provider
Offline mode	Mock planner	Deterministic tests without API cost
Database	SQLite initially	Zero infrastructure, easy reviewer setup
Production DB	PostgreSQL	Concurrent writes and multi-instance scaling
Vector database	Optional Milvus adapter	Useful for larger corpora, unnecessary for 6–12 documents
Retrieval	FTS5/BM25	Fast, explainable, reproducible
Deployment	Docker Compose	Reproducible environment

Important: I would not deploy Milvus just to make the architecture look advanced. Your assignment has a tiny synthetic corpus, and Robosoft explicitly permits keyword search and SQLite. Adding Milvus now would increase setup, testing, and operational complexity without proving better retrieval quality. pulseops-candidate-brief.pdf


Instead, we'll design a Retriever interface so Milvus can be added later without changing the agent's tools.
2. Production-style system architecture
Logical component architecture

3. Agent orchestration design
I recommend a single agent with specialized tools, rather than multiple independent LLM agents.

That is sufficient to demonstrate agentic behavior while reducing latency, token costs, and unpredictable handoffs.
LangGraph workflow
#chatgpt-mermaid-_r_d0_{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;fill:rgb(13, 13, 13);}@keyframes edge-animation-frame{from{stroke-dashoffset:0;}}@keyframes dash{to{stroke-dashoffset:0;}}#chatgpt-mermaid-_r_d0_ .edge-animation-slow{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 50s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-_r_d0_ .edge-animation-fast{stroke-dasharray:9,5!important;stroke-dashoffset:900;animation:dash 20s linear infinite;stroke-linecap:round;}#chatgpt-mermaid-_r_d0_ .error-icon{fill:rgb(243, 243, 243);}#chatgpt-mermaid-_r_d0_ .error-text{fill:rgb(13, 13, 13);stroke:rgb(13, 13, 13);}#chatgpt-mermaid-_r_d0_ .edge-thickness-normal{stroke-width:1px;}#chatgpt-mermaid-_r_d0_ .edge-thickness-thick{stroke-width:3.5px;}#chatgpt-mermaid-_r_d0_ .edge-pattern-solid{stroke-dasharray:0;}#chatgpt-mermaid-_r_d0_ .edge-thickness-invisible{stroke-width:0;fill:none;}#chatgpt-mermaid-_r_d0_ .edge-pattern-dashed{stroke-dasharray:3;}#chatgpt-mermaid-_r_d0_ .edge-pattern-dotted{stroke-dasharray:2;}#chatgpt-mermaid-_r_d0_ .marker{fill:rgb(143, 143, 143);stroke:rgb(143, 143, 143);}#chatgpt-mermaid-_r_d0_ .marker.cross{stroke:rgb(143, 143, 143);}#chatgpt-mermaid-_r_d0_ svg{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:16px;}#chatgpt-mermaid-_r_d0_ p{margin:0;}#chatgpt-mermaid-_r_d0_ .label{font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";color:rgb(13, 13, 13);}#chatgpt-mermaid-_r_d0_ .cluster-label text{fill:rgb(13, 13, 13);}#chatgpt-mermaid-_r_d0_ .cluster-label span{color:rgb(13, 13, 13);}#chatgpt-mermaid-_r_d0_ .cluster-label span p{background-color:transparent;}#chatgpt-mermaid-_r_d0_ .label text,#chatgpt-mermaid-_r_d0_ span{fill:rgb(13, 13, 13);color:rgb(13, 13, 13);}#chatgpt-mermaid-_r_d0_ .node rect,#chatgpt-mermaid-_r_d0_ .node circle,#chatgpt-mermaid-_r_d0_ .node ellipse,#chatgpt-mermaid-_r_d0_ .node polygon,#chatgpt-mermaid-_r_d0_ .node path{fill:rgb(222, 234, 251);stroke:rgb(83, 154, 248);stroke-width:1px;}#chatgpt-mermaid-_r_d0_ .rough-node .label text,#chatgpt-mermaid-_r_d0_ .node .label text,#chatgpt-mermaid-_r_d0_ .image-shape .label,#chatgpt-mermaid-_r_d0_ .icon-shape .label{text-anchor:middle;}#chatgpt-mermaid-_r_d0_ .node .katex path{fill:#000;stroke:#000;stroke-width:1px;}#chatgpt-mermaid-_r_d0_ .rough-node .label,#chatgpt-mermaid-_r_d0_ .node .label,#chatgpt-mermaid-_r_d0_ .image-shape .label,#chatgpt-mermaid-_r_d0_ .icon-shape .label{text-align:center;}#chatgpt-mermaid-_r_d0_ .node.clickable{cursor:pointer;}#chatgpt-mermaid-_r_d0_ .root .anchor path{fill:rgb(143, 143, 143)!important;stroke-width:0;stroke:rgb(143, 143, 143);}#chatgpt-mermaid-_r_d0_ .arrowheadPath{fill:rgb(143, 143, 143);}#chatgpt-mermaid-_r_d0_ .edgePath .path{stroke:rgb(143, 143, 143);stroke-width:1px;}#chatgpt-mermaid-_r_d0_ .flowchart-link{stroke:rgb(143, 143, 143);fill:none;}#chatgpt-mermaid-_r_d0_ .edgeLabel{background-color:rgb(252, 252, 252);text-align:center;}#chatgpt-mermaid-_r_d0_ .edgeLabel p{background-color:rgb(252, 252, 252);}#chatgpt-mermaid-_r_d0_ .edgeLabel rect{opacity:0.5;background-color:rgb(252, 252, 252);fill:rgb(252, 252, 252);}#chatgpt-mermaid-_r_d0_ .labelBkg{background-color:rgba(252, 252, 252, 0.5);}#chatgpt-mermaid-_r_d0_ .cluster rect{fill:rgb(243, 243, 243);stroke:rgba(0, 0, 0, 0.1);stroke-width:1px;}#chatgpt-mermaid-_r_d0_ .cluster text{fill:rgb(13, 13, 13);}#chatgpt-mermaid-_r_d0_ .cluster span{color:rgb(13, 13, 13);}#chatgpt-mermaid-_r_d0_ div.mermaidTooltip{position:absolute;text-align:center;max-width:200px;padding:2px;font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";font-size:12px;background:rgb(243, 243, 243);border:1px solid rgba(0, 0, 0, 0.1);border-radius:2px;pointer-events:none;z-index:100;}#chatgpt-mermaid-_r_d0_ .flowchartTitleText{text-anchor:middle;font-size:18px;fill:rgb(13, 13, 13);}#chatgpt-mermaid-_r_d0_ rect.text{fill:none;stroke-width:0;}#chatgpt-mermaid-_r_d0_ .icon-shape,#chatgpt-mermaid-_r_d0_ .image-shape{background-color:rgb(252, 252, 252);text-align:center;}#chatgpt-mermaid-_r_d0_ .icon-shape p,#chatgpt-mermaid-_r_d0_ .image-shape p{background-color:rgb(252, 252, 252);padding:2px;}#chatgpt-mermaid-_r_d0_ .icon-shape .label rect,#chatgpt-mermaid-_r_d0_ .image-shape .label rect{opacity:0.5;background-color:rgb(252, 252, 252);fill:rgb(252, 252, 252);}#chatgpt-mermaid-_r_d0_ .label-icon{display:inline-block;height:1em;overflow:visible;vertical-align:-0.125em;}#chatgpt-mermaid-_r_d0_ .node .label-icon path{fill:currentColor;stroke:revert;stroke-width:revert;}#chatgpt-mermaid-_r_d0_ .node .neo-node{stroke:rgb(83, 154, 248);}#chatgpt-mermaid-_r_d0_ [data-look="neo"].node rect,#chatgpt-mermaid-_r_d0_ [data-look="neo"].cluster rect,#chatgpt-mermaid-_r_d0_ [data-look="neo"].node polygon{stroke:url(#chatgpt-mermaid-_r_d0_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-_r_d0_ [data-look="neo"].swimlane.cluster rect{filter:none;}#chatgpt-mermaid-_r_d0_ [data-look="neo"].node path{stroke:url(#chatgpt-mermaid-_r_d0_-gradient);stroke-width:1px;}#chatgpt-mermaid-_r_d0_ [data-look="neo"].node .outer-path{filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-_r_d0_ [data-look="neo"].node .neo-line path{stroke:rgb(83, 154, 248);filter:none;}#chatgpt-mermaid-_r_d0_ [data-look="neo"].node circle{stroke:url(#chatgpt-mermaid-_r_d0_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-_r_d0_ [data-look="neo"].node circle .state-start{fill:#000000;}#chatgpt-mermaid-_r_d0_ [data-look="neo"].icon-shape .icon{fill:url(#chatgpt-mermaid-_r_d0_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-_r_d0_ [data-look="neo"].icon-shape .icon-neo path{stroke:url(#chatgpt-mermaid-_r_d0_-gradient);filter:drop-shadow( 1px 2px 2px rgba(185,185,185,1));}#chatgpt-mermaid-_r_d0_ .node text{font-size:14px;font-weight:600;letter-spacing:normal;fill:rgb(0, 79, 153);}#chatgpt-mermaid-_r_d0_ .edgeLabels text{font-size:13px;font-weight:600;letter-spacing:-0.08px;fill:rgb(0, 79, 153);}#chatgpt-mermaid-_r_d0_ .node tspan[font-weight="normal"],#chatgpt-mermaid-_r_d0_ .edgeLabels tspan[font-weight="normal"]{font-weight:600;}#chatgpt-mermaid-_r_d0_ .edgeLabel .label rect{opacity:1;rx:13px;ry:13px;fill:rgb(245, 250, 255);stroke:rgb(206, 219, 229);stroke-width:1px;}#chatgpt-mermaid-_r_d0_ .node rect,#chatgpt-mermaid-_r_d0_ .node circle,#chatgpt-mermaid-_r_d0_ .node ellipse,#chatgpt-mermaid-_r_d0_ .node polygon,#chatgpt-mermaid-_r_d0_ .node path{fill:rgb(229, 243, 255);stroke:rgba(0, 0, 0, 0.1);stroke-width:1px;}#chatgpt-mermaid-_r_d0_ .node rect{rx:16px;ry:16px;}#chatgpt-mermaid-_r_d0_ .mermaid-decision .label-container{fill:rgb(245, 250, 255);stroke:rgb(206, 219, 229);stroke-dasharray:2,2;}#chatgpt-mermaid-_r_d0_ .edgePaths .flowchart-link{stroke:rgb(143, 143, 143);stroke-width:1px;stroke-linecap:round;stroke-linejoin:round;}#chatgpt-mermaid-_r_d0_ .marker{fill:rgb(143, 143, 143);stroke:rgb(143, 143, 143);}#chatgpt-mermaid-_r_d0_ :root{--mermaid-font-family:-apple-system-body,ui-sans-serif,-apple-system,system-ui,"Segoe UI",Helvetica,"Apple Color Emoji",Arial,sans-serif,"Segoe UI Emoji","Segoe UI Symbol";}User RequestValidate InputLoad ConversationPolicy GuardAllowed?Safe RefusalLLM ReasoningTool Calls?Validate Tool ArgumentsExecute ToolsPersist TracesStep Limit?Controlled StopGrounded Final AnswerPersist ResponseNoYesYesNoYesNo





Execution controls
Control	Implementation
Max tool rounds	6, configurable
Tool timeout	Per-tool timeout
Retries	Transient read failures only, bounded
Circuit breaker	Optional for external LLM failures
Duplicate writes	Idempotency key + database uniqueness
Invalid tool arguments	Pydantic validation
Unsafe actions	Policy checks before tool execution
LLM provider failure	Return a controlled error; no automatic write replay
Agent recursion	LangGraph recursion limit
Conversation state	Persisted by conversation ID

For write tools, we'll validate inputs, enforce draft-only status, and commit the artifact and its trace transactionally where possible.
4. Tool contracts
We'll implement five core tools and one optional supporting tool.
Tool	Input	Output
search_docs	query, top_k	Documents, snippets, scores, references
get_service	service_id/name	Ownership, dependencies, SLO
get_pr	pr_number	PR metadata
list_open_prs	optional service	Matching PR records
create_ticket_draft	title, description, priority, team, labels	Persisted ticket ID
summarize_pr	pr_number	Persisted summary ID, risk notes

Example ticket schema
from typing import Literalfrom pydantic import BaseModel, Fieldclass TicketDraftInput(BaseModel):    title: str = Field(min_length=5, max_length=200)    description: str = Field(min_length=10)    priority: Literal["P0", "P1", "P2", "P3"]    labels: list[str] = Field(default_factory=list)    team: str    service_id: str | None = None



We'll add domain-level checks for valid teams, existing services, and whether the requested action is permitted.
5. Database design
For the submission, SQLite will store all durable state. The models will be compatible with a future PostgreSQL migration.
Table	Purpose
conversations	Session metadata
messages	User and assistant messages
agent_runs	Execution status, model, token usage
tool_traces	Tool name, arguments, result, timing
ticket_drafts	Structured ticket drafts
pr_summaries	Structured PR summaries
idempotency_records	Duplicate write prevention

Production-minded database practices include foreign keys, indexes on conversation IDs and timestamps, transactional writes, and explicit schema migrations.

We should also distinguish between SQLite as the assignment's runnable persistence layer and PostgreSQL as the proposed production scaling option. We shouldn't claim PostgreSQL scalability was validated unless we actually test it.
6. Retrieval architecture
For the synthetic knowledge base, I recommend a retrieval interface with two possible implementations.
Implement now
SQLite FTS5 / BM25

Markdown ingestion → text chunking → full-text index → ranked retrieval → source references.

Optional extension
Milvus hybrid retrieval

Markdown ingestion → embeddings → Milvus → dense/sparse retrieval → fusion → optional reranking → source references.

When Milvus becomes worthwhile
Milvus would make sense if we later expanded to thousands of documents, needed semantic matching across terminology, or measured meaningful retrieval improvements over BM25.

For now, we'll establish retrieval metrics first:
- Recall@K
- MRR
- Citation accuracy
- Grounded-answer correctness
- Retrieval latency
That gives us a defensible reason to introduce a vector database rather than adding it without evidence.
7. LLM provider abstraction
We'll support both your API providers using environment variables.
LLM_MODE=mock
LLM_PROVIDER=openai

OPENAI_API_KEY=
OPENAI_MODEL=

XAI_API_KEY=
XAI_MODEL=

DATABASE_URL=sqlite:///./pulseops.db
MAX_TOOL_ROUNDS=6


The provider adapter will normalize model messages, tool-call requests, tool results, usage data, and errors. We will validate each selected model's actual tool-calling and structured-output capabilities before relying on them.

Security: Keep your keys in a local .env file, never commit them, and never paste them into source code or the frontend.

I would use OpenAI as the primary live provider, Grok as a configurable alternative, and mock mode for deterministic CI evaluations. Automatic cross-provider fallback should initially be limited to safe operations because replaying a partially completed write workflow could create duplicate artifacts.
8. Security and reliability checklist
These are the aspects I want us to explicitly verify, not merely mention in documentation.
Area	Required verification
Input validation	Reject invalid requests and malformed tool arguments
Prompt injection	Retrieved documents cannot override system policies
Tool authorization	Only allowlisted tools can execute
Write safety	Draft-only, local persistence
Idempotency	Repeated requests do not create duplicate drafts
Secret protection	.env ignored; logs redact credentials
Error handling	No internal stack traces in API responses
Rate limiting	Basic request protection where appropriate
Timeouts	Bounded model and tool execution
Data integrity	Transactional persistence
Observability	Correlation IDs, structured logs, traces
Cost management	Token usage and model-call counts
Concurrency	Test simultaneous reads and draft creation
API contracts	Validate OpenAPI schemas and response models
Graceful degradation	Mock mode runs without external APIs

For a real production deployment, we would additionally need authentication, authorization, infrastructure monitoring, backup/restore procedures, secrets management, and operational runbooks. The brief explicitly excludes real SSO and production IAM, so those belong in the production-readiness discussion rather than the take-home implementation. pulseops-candidate-brief.pdf

9. Evaluation strategy
The assignment requires at least 12 golden cases. I suggest 16 cases, divided as follows:
Category	Cases	What we verify
Knowledge Q&A	4	Correct answers and references
Service/PR lookup	3	Correct tool routing
Ticket creation	2	Schema and persisted artifacts
PR summarization	2	Summary structure and risk notes
Multi-tool chaining	2	Required tools and execution order
Policy/refusal	2	No unauthorized writes
Tool failure	1	Controlled failure response
Total	16	

We'll run three levels of verification: unit tests for tools and persistence, integration tests for FastAPI and orchestration, and golden evaluations for agent behavior.

The evaluator should report separate scores for answer quality, tool selection, tool order, artifact correctness, and policy compliance. We should avoid treating a successful HTTP response as proof that the agent completed the task correctly.
10. Production readiness versus take-home scope
Implement and test

FastAPI, LangGraph, live/mock LLM adapters, local persistence, safe tools, FTS5 retrieval, UI, structured logging, golden evaluations, Docker, and CI.



Design and document

PostgreSQL migration, horizontal scaling, distributed tracing, production authentication, Redis-backed rate limiting, backup strategy, and Milvus integration.



Only if time remains

Milvus proof of concept, multi-agent handoffs, trace inspection UI, advanced model grading, and load testing.



This distinction matters because Robosoft specifically recommends a complete, reliable core over an incomplete ambitious system. pulseops-candidate-brief.pdf

11. Implementation phases
Build checklist

0 / 7 completed



[ ] Phase 1 — Design and contracts

Requirements matrix, assumptions, architecture ADR, data contracts, golden cases.


[ ] Phase 2 — Repository and synthetic data

uv project, configuration, service inventory, PRs, incidents, Markdown docs.


[ ] Phase 3 — Persistence and tools

SQLAlchemy models, migrations, retrieval, service lookup, draft and PR tools.


[ ] Phase 4 — LangGraph agent

Provider adapters, tool loop, policies, state, retries, traces, stopping rules.


[ ] Phase 5 — API and UI

FastAPI routes, OpenAPI docs, chat interface, session and artifact views.


[ ] Phase 6 — Tests and evaluations

Pytest, 16 golden cases, failure testing, mock/live comparison, CI.


[ ] Phase 7 — Hardening and submission

Docker, clean-clone verification, README, DESIGN, PROCESS, demo script.


Start implementation — Phase 1 
One final principle: we'll keep PROCESS.md truthful, documenting the AI assistance used, the actual tests run, any failures found, and the changes made. That is a major part of this assessment.

The target deliverable is a clean, runnable GitHub repository that a reviewer can clone, start, exercise through the UI, and evaluate with one command — with no API key required for mock mode.