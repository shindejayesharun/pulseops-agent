# On-Call Runbook: Checkout API Latency & Degradation Triage

**Target Service**: `checkout-api` (`svc-checkout-api`)  
**Owner Team**: `payments` | **Slack**: `#payments-oncall` | **PagerDuty**: `PD-CHECKOUT-PRIMARY`

---

## 1. Symptoms & Alert Triggers
- **Alert**: `CheckoutP99LatencyHigh` — Checkout p99 exceeds 1500ms for > 3 minutes.
- **Alert**: `Checkout5xxErrorRateSpike` — HTTP 500/502 rate exceeds 1.5% of total request volume.
- **Customer Impact**: Users report spinners or timeout errors during order placement.

---

## 2. Initial Triage Procedure (First 5 Minutes)

1. **Verify Service Health**:
   ```bash
   curl -s -o /dev/null -w "%{http_code}" https://internal.northstar.net/checkout/health
   # Expected: 200 OK. If 503, inspect pod restarts.
   ```

2. **Inspect Upstream Dependencies**:
   Check Grafana Dashboard `Northstar / Checkout Latency Breakdown`:
   - Is latency isolated to `payment-gateway`? (Look for `upstream_payment_gw_duration_ms`).
   - Is latency isolated to `fraud-detector`? (Look for `upstream_fraud_duration_ms`).

3. **Circuit Breaker Status**:
   If `payment-gateway` latency exceeds 3000ms, ensure the circuit breaker has tripped to OPEN:
   ```bash
   curl -X GET https://internal.northstar.net/checkout/admin/circuit-breakers
   ```
   If not tripped automatically, execute manual fail-open mode:
   ```bash
   curl -X POST https://internal.northstar.net/checkout/admin/circuit-breaker/payment-gw/trip
   ```

4. **Escalation Path**:
   - If downstream database `ledger-db` is saturated, escalate to `@infra-oncall`.
   - If payment gateway upstream provider (Stripe) is degraded, initiate status banner on Northstar Status Page via incident commander.
