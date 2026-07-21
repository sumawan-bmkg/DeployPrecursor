# Daily Operations Checklist — BMKG LAWS V2

## Shift: Morning (07:00 WITA)

| # | Item | Check | Expected | Action if Fail |
|---|---|---|---|---|
| 1 | Systemd Services | `systemctl is-active pocc-dashboard pocc-collector` | active | `systemctl restart <service>` |
| 2 | Backend API | `curl http://localhost:8500/api/health` | `{"status":"OK"}` | Check logs: `journalctl -u pocc-dashboard -n 50` |
| 3 | Predictor | `curl http://localhost:8500/api/predictor` | `"status":"loaded"` | Restart collector: `systemctl restart pocc-collector` |
| 4 | Disk Space | `df -h /opt/pimes/pocc/` | Usage < 80% | Clean logs, rotate if needed |
| 5 | Log Check | `tail -20 /opt/pimes/pocc/collector/collector.log` | No ERROR/TRACEBACK | Investigate first error occurrence |
| 6 | Pipeline Status | `curl http://localhost:8500/api/overview` | `"prediction":"ACTIVE"` | Check scheduler process |

## Shift: Noon (12:00 WITA)

| # | Item | Check | Expected | Action if Fail |
|---|---|---|---|---|
| 1 | Pipeline Runs | `grep "runtime complete" /opt/pimes/pocc/collector/collector.log \| tail -5` | Timestamps < 1h old | Check scheduler: `ps -ef \| grep scheduler` |
| 2 | Validation Errors | `grep -c "ERROR validation" /opt/pimes/pocc/collector/collector.log` | < 50 per hour | Check data source availability |
| 3 | Evidence | `ls /opt/pimes/pocc/output/evidence/ \| wc -l` | Increasing daily | Check evidence_worker |
| 4 | DB Connections | `sudo -u postgres psql -c "SELECT count(*) FROM pg_stat_activity;" -t` | < 20 | Check idle connections |

## Shift: Evening (17:00 WITA)

| # | Item | Check | Expected | Action if Fail |
|---|---|---|---|---|
| 1 | Alerts | `grep -c "WARNING\|ERROR\|CRITICAL" /opt/pimes/pocc/collector/collector.log` | < 10 in last hour | Review each alert |
| 2 | Backup | `ls -la /opt/pimes/backups/ \| tail -1` | File < 24h old | Run manual backup |
| 3 | Summary | All services green | Consistent with morning | Report any changes |

## Shift: Night (22:00 WITA)

| # | Item | Check | Expected | Action if Fail |
|---|---|---|---|---|
| 1 | Cron | `ls -la /opt/pimes/pocc/collector/triggers/` | Clean (no stale triggers) | Remove stale triggers |
| 2 | Overnight | Verify scheduler enabled | `active` | `systemctl restart pocc-collector` |
