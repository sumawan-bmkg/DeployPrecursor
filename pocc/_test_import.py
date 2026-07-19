"""Upload test script to Ubuntu, run it, get result."""
import paramiko, base64, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

# Test script
test = """import sys
sys.path.insert(0, "/opt/pimes/pocc")
from collector.__main__ import CollectorScheduler
print("IMPORT OK")

s = CollectorScheduler()
print("SCHEDULER CREATED")

# Start in background with threads
import threading
def run_bg():
    s.start()

t = threading.Thread(target=run_bg, daemon=True)
t.start()
print("STARTED")
import time; time.sleep(10)
print("RUNNING FOR 10s")
"""

with open("_tmp_test.py", "w") as f:
    f.write(test)

sftp = c.open_sftp()
sftp.put("_tmp_test.py", "/tmp/_test_sched.py")
sftp.close()

_, o, _ = c.exec_command("cd /opt/pimes/pocc && PYTHONPATH=/opt/pimes/pocc PYTHONDONTWRITEBYTECODE=1 /opt/pimes/laws/runtime/.venv/bin/python /tmp/_test_sched.py 2>&1")
print("OUTPUT:", o.read().decode()[:2000])

import os
os.remove("_tmp_test.py")
c.close()
