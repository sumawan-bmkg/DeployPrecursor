"""Check scheduler status after first cycle."""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

checks = [
    ("PROCESS", "ps aux | grep CollectorScheduler | grep -v grep"),
    ("LOG", "tail -40 /opt/pimes/laws/runtime/validation/pdac/scheduler.log 2>/dev/null"),
    ("LOG_SIZE", "wc -c /opt/pimes/laws/runtime/validation/pdac/scheduler.log 2>/dev/null"),
    ("API_HEALTH", "curl -s http://127.0.0.1:8500/api/health 2>/dev/null"),
]

for label, cmd in checks:
    _, o, _ = c.exec_command(cmd)
    out = o.read().decode("utf-8", "replace")[:2000]
    print("\n=== %s ===" % label)
    print(out if out.strip() else "(empty)")

c.close()
