# Northstar Engineering Service Ownership Matrix (RACI)

This document establishes the official ownership, code review requirements, and escalation channels for all services under the Northstar Checkout organization.

---

## 1. Ownership & On-Call Directory

| Service ID | Service Name | Responsible Team | Team Lead | On-Call Handle | Slack Channel |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `svc-checkout-api` | `checkout-api` | `payments` | `@maya_payments` | `@payments-oncall` | `#payments-team` |
| `svc-payment-gw` | `payment-gateway` | `payments` | `@maya_payments` | `@payments-oncall` | `#payments-team` |
| `svc-fraud` | `fraud-detector` | `security` | `@dave_sec` | `@secops-oncall` | `#security-ops` |
| `svc-pricing` | `pricing-engine` | `catalog` | `@elena_cat` | `@catalog-oncall` | `#catalog-dev` |
| `svc-cart` | `cart-service` | `experience` | `@liam_exp` | `@exp-oncall` | `#experience-team`|
| `svc-ledger` | `ledger-db` | `infrastructure` | `@raj_infra` | `@infra-oncall` | `#infra-core` |

---

## 2. Code Review & PR Approval Policies
- **Payment & Ledger Services** (`checkout-api`, `payment-gateway`, `ledger-db`):
  - Minimum 2 approvals required from senior team members.
  - Requires green CI run with 100% passing unit and contract tests.
  - Any PR touching database connection pooling requires explicit sign-off from `@infra-oncall`.
- **Security & Fraud Services** (`fraud-detector`):
  - Mandatory review by `@secops-oncall`.
  - External API integration changes require verification of timeout configs ($\le 500\text{ms}$).
- **Catalog & Experience Services** (`pricing-engine`, `cart-service`):
  - 1 peer approval required.
