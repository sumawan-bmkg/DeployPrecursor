#!/usr/bin/env python3
"""Deploy fixed collector files and run discovery test."""
import paramiko, base64, time, os

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"
POCC = "/opt/pimes/pocc"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=15)

# Clear pycache
c.exec_command("rm -rf /opt/pimes/pocc/collector/__pycache__")

# Upload fixed files
local = r"d:\opt\pimes\pocc\collector"
for fn in ["discovery_worker.py", "download_worker.py", "scheduler_engine.py"]:
    local_path = os.path.join(local, fn)
    remote = POCC + "/collector/" + fn
    with open(local_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    c.exec_command("python3 -c \"import base64; open('%s','wb').write(base64.b64decode('%s'))\"" % (remote, data))
    print("Uploaded:", fn)

time.sleep(2)

# Run discovery
_, o, _ = c.exec_command("PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/opt/pimes/pocc/collector /opt/pimes/laws/runtime/.venv/bin/python3 /opt/pimes/pocc/collector/_test_discovery.py 2>&1")
print("OUTPUT:", o.read().decode()[:2000])

# Check remote_manifest.json
_, o, _ = c.exec_command("ls -la /opt/pimes/laws/runtime/validation/pdac/remote_manifest.json 2>/dev/null")
print("MANIFEST:", o.read().decode()[:200])

c.close()
