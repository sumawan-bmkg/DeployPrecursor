# Maintenance SOP — BMKG LAWS V2

## 1. Scheduled Maintenance Windows
| Type | Frequency | Window | Expected Downtime |
|---|---|---|---|
| Patching | Monthly | Sunday 02:00-04:00 WITA | < 30 min |
| DB Vacuum | Weekly | Monday 03:00-04:00 WITA | < 5 min |
| Log Rotation | Weekly | Tuesday 03:00-03:15 WITA | 0 min |
| DR Drill | Quarterly | Saturday 10:00-12:00 WITA | < 60 min |

## 2. Patch Management
```bash
# Preview updates
apt list --upgradable

# Apply security updates only
apt install --only-upgrade <package>

# Full system update (with restart)
apt update && apt upgrade -y
systemctl daemon-reload
```

## 3. Python Venv Management
```bash
# Activate production venv
source /opt/pimes/laws/runtime/.venv/bin/activate

# List installed
pip list --format=freeze

# Upgrade packages (non-breaking only)
pip install --upgrade <package>
```

## 4. Configuration Backup
```bash
# Before any maintenance
tar czf /opt/pimes/backups/config-$(date +%Y%m%d).tar.gz \
  /opt/pimes/pocc/ \
  /opt/pimes/laws/runtime/ \
  /etc/systemd/system/pocc-*.service

# Restore
tar xzf /opt/pimes/backups/config-<date>.tar.gz -C /
systemctl daemon-reload
```
