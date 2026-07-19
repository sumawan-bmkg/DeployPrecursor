"""Verify BOCC endpoints on Ubuntu."""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

tests = [
    ("HEALTH", "curl -s http://127.0.0.1:8500/api/health"),
    ("COLLECTOR", "curl -s http://127.0.0.1:8500/api/collector | head -c 300"),
    ("CONTROLS", "curl -s http://127.0.0.1:8500/api/controls"),
    ("CONTROL_DISCOVER", "curl -s -X POST http://127.0.0.1:8500/api/collector/control -H 'Content-Type: application/json' -d '{\"action\":\"discover\"}'"),
    ("AUDIT", "curl -s http://127.0.0.1:8500/api/audit | head -c 300"),
    ("PAGE", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/collector"),
    ("DASHBOARD", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/"),
]

for label, cmd in tests:
    _, o, _ = c.exec_command(cmd)
    out = o.read().decode("utf-8", "replace")[:500]
    print("\n=== %s ===" % label)
    print(out if out.strip() else "(empty)")

c.close()
