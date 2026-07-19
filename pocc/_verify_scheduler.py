"""Verify scheduler is running."""
import paramiko, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

# Check processes
_, o, _ = c.exec_command("ps aux | grep -E 'collector|scheduler' | grep -v grep")
procs = o.read().decode().strip()
print("PROCS:", procs[:500] if procs else "NONE")

# Check log
_, o, _ = c.exec_command("tail -25 /opt/pimes/laws/runtime/validation/pdac/scheduler.log 2>/dev/null")
print("LOG:", o.read().decode()[:2000])

# Check API
_, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/collector 2>&1 | python3 -c 'import sys,json;d=json.load(sys.stdin);print(json.dumps({\"workers\":d.get(\"workers\"),\"queue\":d.get(\"queue\")},default=str))' 2>/dev/null")
print("API:", o.read().decode()[:500])

# Check remote manifest freshness
_, o, _ = c.exec_command("ls -la /opt/pimes/laws/runtime/validation/pdac/remote_manifest.json /opt/pimes/laws/runtime/validation/pdac/download_queue.json 2>/dev/null")
print("FILES:", o.read().decode()[:500])

c.close()
