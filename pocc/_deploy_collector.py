#!/usr/bin/env python3
"""Deploy collector package to Ubuntu and run first discovery."""
import paramiko, base64, os, time, glob

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"
POCC = "/opt/pimes/pocc"
LOCAL = r"d:\opt\pimes\pocc"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=15)

# Kill any running scheduler
c.exec_command("pkill -f 'collector.scheduler' 2>/dev/null")
c.exec_command("pkill -f 'collector.__main__' 2>/dev/null")
time.sleep(1)

# Create dirs
c.exec_command("mkdir -p /opt/pimes/pocc/collector /opt/pimes/laws/runtime/validation/pdac/events /opt/pimes/laws/runtime/validation/pdac/certificates /opt/pimes/laws/runtime/validation/pdac/triggers")

# Upload all collector files
files = glob.glob("d:/opt/pimes/pocc/collector/*.py")
uploaded = 0
for local_path in files:
    fn = os.path.basename(local_path)
    remote = POCC + "/collector/" + fn
    with open(local_path, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    cmd = 'python3 -c "import base64; open(\'%s\',\'wb\').write(base64.b64decode(\'%s\'))"' % (remote, data)
    c.exec_command(cmd)
    # Verify
    time.sleep(0.1)
    _, o, _ = c.exec_command("wc -c < '%s'" % remote)
    remote_size = int(o.read().decode().strip())
    local_size = os.path.getsize(local_path)
    status = "OK" if remote_size == local_size else "FAIL(%d!=%d)" % (remote_size, local_size)
    print("%s: %s" % (fn, status))
    uploaded += 1

print("\nUploaded: %d files" % uploaded)

# Run discovery worker standalone
print("\nRunning discovery...")
_, o, _ = c.exec_command('''cd /opt/pimes/pocc && /opt/pimes/laws/runtime/.venv/bin/python3 << 'EOF'
import sys
sys.path.insert(0, ".")
from discovery_worker import DiscoveryWorker
from scheduler_engine import manifest

w = DiscoveryWorker("discovery_test", manifest, 1)
result = w.execute()
import json
print(json.dumps({
    "stations": result.get("total_stations", 0),
    "files": result.get("total_files", 0),
    "size_gb": result.get("total_size_gb", 0),
    "latency": result.get("latency", 0),
    "success": True
}, indent=2))
EOF''')
output = o.read().decode("utf-8", "replace")
print("OUTPUT:", output[:2000])

# Save manifest
manifest.set("remote", {"discovery_run": time.time()})
manifest.set("last_discovery", time.time())
manifest.save()

c.close()
print("\nDone!")
