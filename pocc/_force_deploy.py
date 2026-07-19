#!/usr/bin/env python3
"""Force deploy backend main.py with cat base64."""
import paramiko, base64, os

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

# Upload main.py via stdin (reliable)
local = r"d:\opt\pimes\pocc\backend\main.py"
remote = "/opt/pimes/pocc/backend/main.py"

with open(local, "rb") as f:
    content = f.read()

print("Local size:", len(content))

# Write via base64 in stdin to avoid quoting issues
data = base64.b64encode(content).decode()
cmd = 'python3 -c "import base64; open(\\\"%s\\\",\\\"wb\\\").write(base64.b64decode(\\\"%s\\\"))"' % (remote, data)
_, o, e = c.exec_command(cmd)
err = e.read().decode()
if err.strip():
    print("ERR:", err[:200])

# Verify
_, o, _ = c.exec_command("wc -c < /opt/pimes/pocc/backend/main.py")
size = o.read().decode().strip()
print("Remote size:", size)

if size.strip() == str(len(content)):
    # Restart
    _, o, _ = c.exec_command("fuser -k 8500/tcp 2>/dev/null; sleep 1")
    _, o, _ = c.exec_command("cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500 > /opt/pimes/pocc/pocc.log 2>&1 </dev/null &")
    _, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/health")
    print("HEALTH:", o.read().decode()[:200])
else:
    print("SIZE MISMATCH — retry")
    print("Expected:", len(content), "Got:", size)

c.close()
