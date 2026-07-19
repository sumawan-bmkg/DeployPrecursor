"""Verify collector page after fix."""
import paramiko

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

_, o, _ = c.exec_command("curl -s -w '\\nHTTP_CODE:%{http_code}' http://127.0.0.1:8500/collector 2>&1 | tail -3")
print("COLLECTOR PAGE:", o.read().decode()[:200])

_, o, _ = c.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/api/collector 2>/dev/null")
print("API:", o.read().decode()[:50])

c.close()
