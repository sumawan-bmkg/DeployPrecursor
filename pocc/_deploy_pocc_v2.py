#!/usr/bin/env python3
"""Deploy POCC v2 to Ubuntu."""
import paramiko, base64, os, glob

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=15)

POCC = "/opt/pimes/pocc"
LOCAL = r"d:\opt\pimes\pocc"

# Kill old POCC
c.exec_command("pkill -f 'uvicorn.*backend.main' 2>/dev/null; sleep 1")

# Upload files
files_to_upload = [
    "backend/main.py",
    "backend/static/css/pocc.css",
    "backend/static/js/pocc.js",
    "backend/static/img/logo_bmkg.svg",
] + glob.glob("backend/templates/*.html", root_dir=LOCAL)

for rel_path in files_to_upload:
    local = os.path.join(LOCAL, rel_path)
    remote = os.path.join(POCC, rel_path.replace("\\", "/"))
    with open(local, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    # Ensure remote dir exists
    c.exec_command("mkdir -p " + os.path.dirname(remote))
    cmd = 'python3 -c "import base64; open(\\\"%s\\\",\\\"wb\\\").write(base64.b64decode(\\\"%s\\\"))"' % (remote, data)
    c.exec_command(cmd)
    print("OK:", rel_path)

# Install deps
c.exec_command("cd %s && %s -m pip install fastapi uvicorn jinja2 psutil websockets -q" % (
    POCC, "/opt/pimes/laws/runtime/.venv/bin/python"))

# Start
c.exec_command("cd %s && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500 > %s/pocc.log 2>&1 & sleep 2" % (POCC, POCC))

# Verify
_, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/ | head -c 200")
print("Frontend:", o.read().decode()[:200])
_, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/health")
print("API:", o.read().decode()[:200])
c.close()
print("\n✅ POCC v2 deployed!")
