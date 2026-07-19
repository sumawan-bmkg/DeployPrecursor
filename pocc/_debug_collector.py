"""Debug POCC collector endpoint + scheduler status."""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

checks = [
    ("COLLECTOR_API", "curl -s -w '\\nHTTP_CODE:%{http_code}' http://127.0.0.1:8500/api/collector 2>&1 | tail -20"),
    ("HEALTH", "curl -s http://127.0.0.1:8500/api/health 2>/dev/null"),
    ("PAGES", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/collector 2>/dev/null"),
    ("LOG", "tail -30 /opt/pimes/laws/runtime/validation/pdac/scheduler.log 2>/dev/null"),
    ("SCHEDULER_PROC", "ps aux | grep _run_scheduler | grep -v grep | head -2"),
    ("POCC_LOG", "tail -10 /opt/pimes/pocc/pocc.log 2>/dev/null"),
]

for label, cmd in checks:
    _, o, _ = c.exec_command(cmd)
    out = o.read().decode("utf-8", "replace")[:2000]
    print("\n=== %s ===" % label)
    print(out if out.strip() else "(empty)")

c.close()
