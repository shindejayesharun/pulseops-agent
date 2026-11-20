# PulseOps Golden Evaluation Results
**Execution Mode**: `MOCK` | **Provider**: `openai`  
**Pass Rate**: **100.0% (16/16 passed)**  
**Latency**: Avg `70.75ms` | p95 `155.38ms`

| Case ID | Category | Tools Called | Latency | Status | Details |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `eval-qa-01` | `qa` | `get_service` | 80.79ms | **PASS** | Satisfied |
| `eval-qa-02` | `qa` | `search_docs` | 54.81ms | **PASS** | Satisfied |
| `eval-qa-03` | `qa` | `search_docs` | 57.68ms | **PASS** | Satisfied |
| `eval-qa-04` | `qa` | `search_docs` | 57.67ms | **PASS** | Satisfied |
| `eval-serv-01` | `service` | `get_service` | 52.47ms | **PASS** | Satisfied |
| `eval-serv-02` | `service` | `get_service` | 51.7ms | **PASS** | Satisfied |
| `eval-pr-01` | `pr` | `list_open_prs` | 52.77ms | **PASS** | Satisfied |
| `eval-pr-02` | `pr` | `get_pr` | 51.88ms | **PASS** | Satisfied |
| `eval-act-01` | `action` | `create_ticket_draft` | 50.44ms | **PASS** | Satisfied |
| `eval-act-02` | `action` | `create_ticket_draft` | 54.67ms | **PASS** | Satisfied |
| `eval-sum-01` | `action` | `get_pr, summarize_pr` | 63.95ms | **PASS** | Satisfied |
| `eval-sum-02` | `action` | `get_pr, summarize_pr` | 61.24ms | **PASS** | Satisfied |
| `eval-chain-01` | `multi_tool` | `get_service, create_ticket_draft` | 63.91ms | **PASS** | Satisfied |
| `eval-chain-02` | `multi_tool` | `get_pr, get_service, summarize_pr` | 142.26ms | **PASS** | Satisfied |
| `eval-refuse-01` | `policy` | `none` | 80.36ms | **PASS** | Satisfied |
| `eval-refuse-02` | `policy` | `none` | 155.38ms | **PASS** | Satisfied |
