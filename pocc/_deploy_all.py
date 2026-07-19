#!/usr/bin/env python3
"""One-shot POCC deploy: create dirs, upload files, restart."""
import paramiko, base64, os, time

POCC = "/opt/pimes/pocc"
LOCAL = r"d:\opt\pimes\pocc"

# All files to deploy
FILES = [
    ("backend/static/css/pocc.css", True),
    ("backend/static/js/pocc.js", True),
    ("backend/static/img/logo_bmkg.svg", True),
    ("backend/templates/base.html", True),
    ("backend/templates/dashboard.html", True),
    ("backend/templates/pipeline.html", True),
    ("backend/templates/scientific.html", True),
    ("backend/templates/burnin.html", True),
    ("backend/templates/stations.html", True),
    ("backend/templates/collector.html", True),
    ("backend/templates/artifacts.html", True),
    ("backend/templates/analytics.html", True),
    ("backend/templates/shadow.html", True),
    ("backend/templates/release.html", True),
    ("backend/templates/system.html", True),
    ("backend/templates/audit.html", True),
    ("backend/main.py", False),  # already uploaded
]

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

# Kill old server
c.exec_command("pkill -f 'uvicorn.*backend.main' 2>/dev/null")
time.sleep(1)

# Create all directories first
dirs = set()
for rel_path, _ in FILES:
    full = POCC + "/" + rel_path.replace("\\", "/")
    dirs.add(os.path.dirname(full))
for d in sorted(dirs):
    c.exec_command("mkdir -p " + d)
    time.sleep(0.1)
print("Dirs created:", len(dirs))

# Upload each file
uploaded = 0
for rel_path, do_upload in FILES:
    local = os.path.join(LOCAL, rel_path.replace("\\", "/"))
    remote = POCC + "/" + rel_path.replace("\\", "/")
    if not os.path.exists(local):
        print("MISSING:", local)
        continue
    with open(local, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    cmd = 'python3 -c "import base64; open(\\\"%s\\\",\\\"wb\\\").write(base64.b64decode(\\\"%s\\\"))"' % (remote, data)
    _, o, _ = c.exec_command(cmd)
    # Verify
    _, o, _ = c.exec_command("wc -c < '%s' 2>/dev/null || echo 0" % remote)
    remote_size = int(o.read().decode().strip())
    local_size = os.path.getsize(local)
    status = "OK" if remote_size == local_size else "MISMATCH(%d!=%d)" % (remote_size, local_size)
    print("  %s: %s" % (rel_path.split("/")[-1], status))
    uploaded += 1

print("\nUploaded: %d files" % uploaded)

# Start server
c.exec_command("cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500 > /opt/pimes/pocc/pocc.log 2>&1 </dev/null &")
time.sleep(3)

# Verify
_, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/health 2>&1")
health = o.read().decode()[:300]
print("HEALTH:", health)
_, o, _ = c.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/ 2>&1")
print("HTTP:", o.read().decode()[:50])
c.close()
