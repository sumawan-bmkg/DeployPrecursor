# Incident Response SOP — BMKG LAWS V2

## 1. Severity Levels

| Level | Definition | Response Time | Examples |
|---|---|---|---|
| **P0** | System down / data loss | < 15 min | Collector crash, DB corruption |
| **P1** | Major feature degradation | < 1 hour | Prediction failures, dashboard down |
| **P2** | Partial feature degradation | < 4 hours | Validation errors, latency spikes |
| **P3** | Minor issue / cosmetic | < 24 hours | Log warnings, non-critical errors |

## 2. Escalation Matrix

| Role | P0 | P1 | P2 | P3 |
|---|---|---|---|---|
| Operator | Immediate response | Within 15 min | Within 1 hour | Next day |
| DevOps Lead | 15 min | 30 min | 2 hours | 24 hours |
| System Architect | 30 min | 1 hour | 4 hours | Notification |
| BMKG Management | 1 hour | Report | Summary | Weekly |

## 3. Runbooks

### 3.1 P0 — Collector Crash
```bash
# 1. Check status
systemctl status pocc-collector
journalctl -u pocc-collector -n 50 --no-pager

# 2. Restart
systemctl restart pocc-collector

# 3. Verify
systemctl is-active pocc-collector  # Should say "active"

# 4. Check pipeline resumption
tail -f /opt/pimes/pocc/collector/collector.log
```

### 3.2 P0 — DB Failure
```bash
# 1. Check PostgreSQL
sudo -u postgres psql -c "SELECT 1;"  # Should return 1

# 2. Check service
systemctl status postgresql@16-main

# 3. Restart
systemctl restart postgresql@16-main

# 4. Verify connection
curl http://localhost:8500/api/predictor
```

### 3.3 P1 — Disk Full (>90%)
```bash
# 1. Find large files
du -sh /opt/pimes/pocc/logs/* | sort -rh | head -5

# 2. Rotate logs
logrotate -f /etc/logrotate.d/pocc-collector
logrotate -f /etc/logrotate.d/pocc-dashboard

# 3. Clean old backups (keep last 7)
find /opt/pimes/backups/ -name "*.sql.gz" -mtime +7 -delete
```

### 3.4 P1 — Prediction Failure
```bash
# 1. Check predictor
curl http://localhost:8500/api/predictor  # Should show "loaded"

# 2. Check inference worker
grep "inference" /opt/pimes/pocc/collector/collector.log | tail -10

# 3. Check decision engine
grep "decision" /opt/pimes/pocc/collector/collector.log | tail -10
```
