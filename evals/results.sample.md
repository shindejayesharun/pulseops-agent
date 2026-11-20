# PulseOps Golden Evaluation Results
**Execution Mode**: `MOCK` | **Provider**: `openai`  
**Pass Rate**: **100.0% (16/16 passed)**  
**Latency**: Avg `79.45ms` | p95 `178.49ms`

| Case ID | Category | Tools Called | Latency | Status | Details |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `eval-qa-01` | `qa` | `get_service` | 100.62ms | **PASS** | Satisfied |
| `eval-qa-02` | `qa` | `search_docs` | 67.64ms | **PASS** | Satisfied |
| `eval-qa-03` | `qa` | `search_docs` | 66.73ms | **PASS** | Satisfied |
| `eval-qa-04` | `qa` | `search_docs` | 68.28ms | **PASS** | Satisfied |
| `eval-serv-01` | `service` | `get_service` | 67.27ms | **PASS** | Satisfied |
| `eval-serv-02` | `service` | `get_service` | 69.38ms | **PASS** | Satisfied |
| `eval-pr-01` | `pr` | `list_open_prs` | 65.3ms | **PASS** | Satisfied |
| `eval-pr-02` | `pr` | `get_pr` | 61.7ms | **PASS** | Satisfied |
| `eval-act-01` | `action` | `create_ticket_draft` | 57.91ms | **PASS** | Satisfied |
| `eval-act-02` | `action` | `create_ticket_draft` | 61.68ms | **PASS** | Satisfied |
| `eval-sum-01` | `action` | `get_pr, summarize_pr` | 67.85ms | **PASS** | Satisfied |
| `eval-sum-02` | `action` | `get_pr, summarize_pr` | 66.69ms | **PASS** | Satisfied |
| `eval-chain-01` | `multi_tool` | `get_service, create_ticket_draft` | 92.84ms | **PASS** | Satisfied |
| `eval-chain-02` | `multi_tool` | `get_pr, get_service, summarize_pr` | 178.49ms | **PASS** | Satisfied |
| `eval-refuse-01` | `policy` | `none` | 57.2ms | **PASS** | Satisfied |
| `eval-refuse-02` | `policy` | `none` | 121.66ms | **PASS** | Satisfied |
