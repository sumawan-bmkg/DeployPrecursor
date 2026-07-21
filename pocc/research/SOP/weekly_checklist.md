# Weekly Operations Checklist — BMKG LAWS V2

## Day: Monday — DB Maintenance

| # | Item | Command | Expected |
|---|---|---|---|
| 1 | VACUUM ANALYZE | `sudo -u postgres psql -d pimes -c "VACUUM ANALYZE;"` | VACUUM |
| 2 | Index rebuild | `sudo -u postgres psql -d pimes -c "REINDEX DATABASE pimes;"` | REINDEX |
| 3 | DB Size | `sudo -u postgres psql -d pimes -c "SELECT pg_size_pretty(pg_database_size('pimes'));"` | < 10GB |

## Day: Tuesday — Log Rotation

| # | Item | Command | Expected |
|---|---|---|---|
| 1 | Rotate collector.log | `logrotate -f /etc/logrotate.d/pocc-collector` | OK |
| 2 | Rotate dashboard.log | `logrotate -f /etc/logrotate.d/pocc-dashboard` | OK |
| 3 | Check journal | `journalctl --disk-usage` | < 500MB |

## Day: Wednesday — Performance Baseline

| # | Item | Command | Expected |
|---|---|---|---|
| 1 | API Latency | `ab -n 100 http://localhost:8500/api/health` | p95 < 200ms |
| 2 | Load Avg | `uptime` | Load < #cores |
| 3 | Pipeline timing | Check `__main__.py` logs for cycle duration | < 1800s |

## Day: Thursday — Security Check

| # | Item | Command | Expected |
|---|---|---|---|
| 1 | Failed SSH | `lastb \| wc -l` | < 10 |
| 2 | Open ports | `ss -tlnp` | Known ports only |
| 3 | Updates | `apt list --upgradable \| wc -l` | < 10 |

## Day: Friday — DR Drill

| # | Item | Command | Expected |
|---|---|---|---|
| 1 | Backup restore test | Verify SQL file loads in test DB | 0 errors |
| 2 | Failover test | Stop collector → restart → verify state | Automatic recovery |
