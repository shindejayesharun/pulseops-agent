# Incident Response & Severity Guide

## 1. Incident Severity Definitions

| Severity | Definition | Target MTTA | Target MTTR | Examples |
| :--- | :--- | :--- | :--- | :--- |
| **P0** | Critical company-wide outage. Complete loss of revenue or data integrity. | < 5 mins | < 1 hour | Complete checkout unavailability, database data corruption. |
| **P1** | Major degradation affecting > 10% of users or core payment settlement failure. | < 15 mins | < 2 hours | Checkout latency > 4s, payment gateway dropping 15% of transactions. |
| **P2** | Significant feature impairment with existing manual workaround. | < 30 mins | < 6 hours | Fraud detector falling back to default accept, coupon discounts failing. |
| **P3** | Minor operational defect, non-critical documentation gap, cosmetic UI issue. | < 4 hours | < 3 days | Missing runbook documentation, internal reporting dashboard delay. |
| **P4** | Low-priority maintenance, non-impacting technical debt. | < 24 hours | Next sprint | Deprecated API token cleanup, log format improvements. |

---

## 2. Escalation & Communication Protocols
1. **Incident Commander (IC)**:
   - For all P0 and P1 incidents, the on-call engineer for the affected service automatically assumes IC until relieved.
   - IC creates a dedicated incident channel: `#inc-<date>-<brief-slug>`.
2. **External Communications Policy**:
   - **STRICT PROHIBITION**: Engineers must **never** post incident details, root causes, or system statuses to public social media accounts (Twitter/X, LinkedIn) or unvetted external forums.
   - All external communications are governed exclusively by the PR & Communications Team via `status.northstar.com`.
3. **Drafting Incident Tickets**:
   - Every active incident requires an internal ticket draft with:
     - Clear descriptive title matching affected services.
     - Severity tier (`P0`-`P4`).
     - Linked service ID.
     - Responsible owner team.
