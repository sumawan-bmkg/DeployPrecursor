"""Direct start — avoid module import issues."""
import paramiko, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

# Kill old
c.exec_command("pkill -f 'collector' 2>/dev/null")
time.sleep(2)

# Create __init__.py
c.exec_command("touch /opt/pimes/pocc/collector/__init__.py")
time.sleep(1)

# Start directly as script (bypass module)
start_cmd = """cd /opt/pimes/pocc && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/opt/pimes/pocc nohup /opt/pimes/laws/runtime/.venv/bin/python -u -c '
import sys
sys.path.insert(0, "/opt/pimes/pocc")
from collector.__main__ import CollectorScheduler
s = CollectorScheduler()
s.start()
' > /opt/pimes/laws/runtime/validation/pdac/scheduler.log 2>&1 & echo RUNNING"""
_, o, _ = c.exec_command(start_cmd)
print("START:", o.read().decode()[:200])
time.sleep(5)

# Check
_, o, _ = c.exec_command("ps aux | grep '__main__' | grep -v grep | wc -l")
print("PROC COUNT:", o.read().decode().strip())

_, o, _ = c.exec_command("tail -20 /opt/pimes/laws/runtime/validation/pdac/scheduler.log 2>/dev/null")
print("LOG:", o.read().decode()[:1500])

_, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/collector 2>&1 | head -c 400")
print("API:", o.read().decode()[:400])

c.close()
