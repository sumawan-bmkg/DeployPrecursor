#!/usr/bin/env python3
"""Collector Command Center — full rewrite."""
import paramiko, base64, os, time

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"
POCC = "/opt/pimes/pocc"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=15)

# Upload:
# 1. enhanced backend main.py (with rich collector API)
# 2. collector.html (Command Center)
# 3. collector.js (live refresh + actions)
# 4. collector.css (if exists)

files = {
    "backend/main.py": r"d:\opt\pimes\pocc\backend\main.py",
    "backend/templates/collector.html": r"d:\opt\pimes\pocc\backend\templates\collector.html",
    "backend/static/js/collector.js": r"d:\opt\pimes\pocc\backend\static\js\collector.js",
}

for rel, local in files.items():
    if not os.path.exists(local):
        print("SKIP (not yet written):", rel)
        continue
    remote = f"{POCC}/{rel}"
    with open(local, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    
    # Upload via sftp script
    script = 'import base64; open("%s","wb").write(base64.b64decode("%s"))' % (remote, data)
    with open("_tmp_up.py", "w") as f:
        f.write(script)
    sftp = c.open_sftp()
    sftp.put("_tmp_up.py", "/tmp/_up.py")
    sftp.close()
    c.exec_command("python3 /tmp/_up.py && rm /tmp/_up.py")
    time.sleep(0.3)
    os.remove("_tmp_up.py")
    
    # Verify
    _, o, _ = c.exec_command("wc -c < %s" % remote)
    rs = o.read().decode().strip()
    ls = str(os.path.getsize(local))
    print("  %s: %s" % (rel.split("/")[-1], "OK" if rs == ls else "FAIL(%s!=%s)" % (rs, ls)))

# Restart POCC
c.exec_command("pkill -f 'uvicorn.*backend.main' 2>/dev/null; sleep 1")
c.exec_command("cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500 > /opt/pimes/pocc/pocc.log 2>&1 </dev/null &")
time.sleep(3)

# Verify
_, o, _ = c.exec_command("curl -s -o /dev/null -w '%%{http_code}' http://127.0.0.1:8500/collector 2>/dev/null")
print("COLLECTOR PAGE:", o.read().decode()[:50])
_, o, _ = c.exec_command("curl -s -o /dev/null -w '%%{http_code}' http://127.0.0.1:8500/api/collector 2>/dev/null")
print("COLLECTOR API:", o.read().decode()[:50])

c.close()
print("\nDone!")
