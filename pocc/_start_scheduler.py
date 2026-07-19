#!/usr/bin/env python3
"""Start full collector scheduler on Ubuntu."""
import paramiko, base64, time, os

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"
POCC = "/opt/pimes/pocc"
LOCAL_COLLECTOR = r"d:\opt\pimes\pocc\collector"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=15)

# Kill old
c.exec_command("pkill -f 'collector' 2>/dev/null")
time.sleep(1)

# Clear stale state
c.exec_command("rm -f /opt/pimes/laws/runtime/validation/pdac/download_queue.json")
c.exec_command("rm -rf /opt/pimes/pocc/collector/__pycache__")
time.sleep(1)

# Upload ALL collector files
for fn in os.listdir(LOCAL_COLLECTOR):
    if fn.endswith('.py') and not fn.startswith('_'):
        lpath = os.path.join(LOCAL_COLLECTOR, fn)
        remote = f"{POCC}/collector/{fn}"
        with open(lpath, "rb") as f:
            data = base64.b64encode(f.read()).decode()
        # Write via script file to avoid quoting hell
        upload_script = 'import base64; open("%s","wb").write(base64.b64decode("%s"))' % (remote, data)
        with open("_tmp_upload.py", "w") as f:
            f.write(upload_script)
        # Upload the script via sftp (small), then run it
        sftp = c.open_sftp()
        sftp.put("_tmp_upload.py", "/tmp/_up.py")
        sftp.close()
        os.remove("_tmp_upload.py")
        c.exec_command("python3 /tmp/_up.py && rm /tmp/_up.py")
        time.sleep(0.2)
        _, o, _ = c.exec_command("wc -c < %s" % remote)
        rs = o.read().decode().strip()
        ls = str(os.path.getsize(lpath))
        print("  %s: %s" % (fn, "OK" if rs == ls else "FAIL(%s!=%s)" % (rs, ls)))

print("\nFiles uploaded. Starting scheduler...")

# Create start script
start_script = '''#!/bin/bash
cd %s/collector
export PYTHONPATH=%s/collector
export PYTHONDONTWRITEBYTECODE=1
nohup /opt/pimes/laws/runtime/.venv/bin/python -u -m collector.__main__ > /opt/pimes/laws/runtime/validation/pdac/scheduler.log 2>&1 &
echo "PID=$!"
sleep 3
tail -5 /opt/pimes/laws/runtime/validation/pdac/scheduler.log
''' % (POCC, POCC)

with open("_tmp_start.sh", "w") as f:
    f.write(start_script)
sftp = c.open_sftp()
sftp.put("_tmp_start.sh", "/tmp/_start.sh")
sftp.close()
os.remove("_tmp_start.sh")

_, o, _ = c.exec_command("bash /tmp/_start.sh && rm /tmp/_start.sh")
print("START:", o.read().decode()[:1000])

time.sleep(5)

# Verify
_, o, _ = c.exec_command("ps aux | grep '__main__' | grep -v grep")
procs = o.read().decode().strip()
print("PROCESSES:", procs[:200] if procs else "NONE")

_, o, _ = c.exec_command("cat /opt/pimes/laws/runtime/validation/pdac/scheduler.log 2>/dev/null | tail -15")
print("LOG:", o.read().decode()[:1500])

_, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/collector 2>&1 | head -c 500")
print("API:", o.read().decode()[:500])

c.close()
print("\nDone!")
