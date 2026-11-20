# Database Failover Runbook: Ledger DB

**Target Service**: `ledger-db` (`svc-ledger`)  
**Database Engine**: PostgreSQL 16 Cluster with Streaming Replication  
**Owner**: `@infra-oncall`

---

## 1. Failover Triggers
- Primary node unresponsive to health check ping for > 30 seconds.
- Storage disk volume corruption or disk write-lock event.
- Replication lag on hot standby is $\le 100\text{ms}$.

---

## 2. Manual Failover Execution Steps

1. **Verify Standby Replication Status**:
   ```bash
   patronictl -c /etc/patroni/ledger.yml topology
   ```
   Confirm standby node `ledger-db-replica-01` is in `running` state with `lag < 1MB`.

2. **Execute Failover via Patroni**:
   ```bash
   patronictl -c /etc/patroni/ledger.yml failover ledger-cluster --candidate ledger-db-replica-01
   ```

3. **Flush Connection Pools**:
   Restart PgBouncer connection pooling routers to drain stale sockets:
   ```bash
   ansible-playbook -i inventory/prod pgbouncer_reload.yml
   ```

4. **Verify Application Connectivity**:
   ```bash
   curl https://internal.northstar.net/payment-gateway/health/db
   # Expected: {"status": "HEALTHY", "db_primary": "ledger-db-replica-01"}
   ```
