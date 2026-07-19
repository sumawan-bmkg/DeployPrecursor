import paramiko, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

# Kill existing
c.exec_command("pkill -f 'uvicorn' 2>/dev/null")
time.sleep(1)

# Test import
_, o, _ = c.exec_command("cd /opt/pimes/pocc && /opt/pimes/laws/runtime/.venv/bin/python -c 'from backend.main import app; print(\"IMPORT OK\")' 2>&1")
print("IMPORT:", o.read().decode()[:200])

# Start
c.exec_command("cd /opt/pimes/pocc && /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500 &>/opt/pimes/pocc/pocc.log &")
time.sleep(3)

# Check
_, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/health 2>&1")
print("HEALTH:", o.read().decode()[:300])

# Also check frontend
_, o, _ = c.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/ 2>&1")
print("HTTP:", o.read().decode()[:50])

c.close()
