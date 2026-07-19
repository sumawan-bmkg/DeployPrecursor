"""Upload __main__.py and start scheduler."""
import paramiko, base64, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

# Kill old
c.exec_command("pkill -f collector 2>/dev/null")
time.sleep(1)

# Upload updated __main__.py
lpath = r"d:\opt\pimes\pocc\collector\__main__.py"
with open(lpath, "rb") as f:
    data = base64.b64encode(f.read()).decode()
    
# Use heredoc to avoid quote issues
script = '''import base64; open("/opt/pimes/pocc/collector/__main__.py","wb").write(base64.b64decode("%s"))''' % data
with open("_tmp_up.py", "w") as f:
    f.write(script)

sftp = c.open_sftp()
sftp.put("_tmp_up.py", "/tmp/_up.py")
sftp.close()

_, o, _ = c.exec_command("python3 /tmp/_up.py && rm /tmp/_up.py")
print("Upload:", o.read().decode()[:200])

# Verify
_, o, _ = c.exec_command("head -15 /opt/pimes/pocc/collector/__main__.py")
print("Head:", o.read().decode()[:500])

import os; os.remove("_tmp_up.py")

# Now test import
_, o, _ = c.exec_command("cd /opt/pimes/pocc && PYTHONPATH=/opt/pimes/pocc /opt/pimes/laws/runtime/.venv/bin/python -c 'from collector.__main__ import CollectorScheduler; print(\"IMPORT OK\")' 2>&1")
print("IMPORT:", o.read().decode()[:500])

# Start
_, o, _ = c.exec_command("cd /opt/pimes/pocc && PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/opt/pimes/pocc nohup /opt/pimes/laws/runtime/.venv/bin/python -u -c 'from collector.__main__ import CollectorScheduler;CollectorScheduler().start()' > /opt/pimes/laws/runtime/validation/pdac/scheduler.log 2>&1 & echo RUNNING")
print("START:", o.read().decode()[:100])
time.sleep(5)

# Check
_, o, _ = c.exec_command("ps aux | grep 'CollectorScheduler' | grep -v grep | wc -l")
print("PROC:", o.read().decode().strip())

_, o, _ = c.exec_command("tail -20 /opt/pimes/laws/runtime/validation/pdac/scheduler.log 2>/dev/null")
print("LOG:", o.read().decode()[:2000])

_, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/collector 2>&1 | python3 -c 'import sys,json;d=json.load(sys.stdin);print(json.dumps({k:d.get(k) for k in[\"workers\",\"queue\"]},default=str))' 2>/dev/null")
print("API:", o.read().decode()[:500])

c.close()
