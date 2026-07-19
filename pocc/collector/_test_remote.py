import paramiko, base64, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

# Create test script
script = """#!/usr/bin/env python3
import sys
sys.path.insert(0, "/opt/pimes/pocc/collector")
from discovery_worker import DiscoveryWorker
from scheduler_engine import manifest

print("IMPORT OK")
w = DiscoveryWorker("test", manifest, interval=1)
try:
    r = w.execute()
    print("RESULT:", r.get("total_files", 0), "files")
    print("STATIONS:", r.get("total_stations", 0))
except Exception as e:
    print("FAIL:", str(e)[:200])
"""

with open("d:/opt/pimes/pocc/collector/_test_discovery.py", "w") as f:
    f.write(script)

with open("d:/opt/pimes/pocc/collector/_test_discovery.py", "rb") as f:
    data = base64.b64encode(f.read()).decode()

c.exec_command("python3 -c \"import base64; open('/opt/pimes/pocc/collector/_test_discovery.py','wb').write(base64.b64decode('%s'))\"" % data)
time.sleep(1)

_, o, _ = c.exec_command("PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/opt/pimes/pocc/collector /opt/pimes/laws/runtime/.venv/bin/python3 /opt/pimes/pocc/collector/_test_discovery.py 2>&1")
print("OUTPUT:", o.read().decode()[:2000])
c.close()
