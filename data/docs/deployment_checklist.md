# Northstar Production Deployment & Release Checklist

Every service release deployed to the Northstar Checkout cluster must strictly follow this checklist to prevent unexpected downtime and transaction loss.

---

## 1. Pre-Deployment Verification
- [ ] Pull request has been approved by at least 2 team members (including domain owner).
- [ ] Automated CI tests (unit, integration, and contract tests) have passed 100%.
- [ ] Database migrations have been tested against staging read-replica clone.
- [ ] Zero breaking changes in public API contracts without a version bump (e.g. `/v2/` $\to$ `/v3/`).

---

## 2. Deployment Execution Steps
1. **Deploy to Canary Pods (5% Traffic)**:
   ```bash
   kubectl set image deployment/checkout-api checkout-api=northstar/checkout-api:v2.4.1 -n prod-canary
   ```
2. **Monitor Error Rates for 10 Minutes**:
   - HTTP 5xx error rate must remain below 0.05%.
   - Latency p95 must not exceed baseline by > 10%.
3. **Promote to Full Cluster (100% Traffic)**:
   ```bash
   kubectl rollout resume deployment/checkout-api -n prod
   ```

---

## 3. Rollback Protocol
If HTTP 5xx rate exceeds 0.5% at any point during rollout:
```bash
kubectl rollout undo deployment/checkout-api -n prod
```
Notify `#payments-team` and open a P1 or P2 incident ticket.
