"""BOCC deploy — upload files via sftp."""
import paramiko, os, time

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"
POCC = "/opt/pimes/pocc"
LOCAL = r"d:\opt\pimes\pocc"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=10)
sftp = c.open_sftp()

def up(local_rel, remote_rel):
    local_path = os.path.join(LOCAL, local_rel.replace("/", "\\"))
    remote_path = f"{POCC}/{remote_rel}"
    try:
        sftp.put(local_path, remote_path)
        sz = sftp.stat(remote_path).st_size
        print(f"  {remote_rel.split('/')[-1]}: {sz} bytes")
    except Exception as e:
        print(f"  {remote_rel.split('/')[-1]}: ERROR {e}")

up("backend/main.py", "backend/main.py")
up("backend/static/css/bocc.css", "backend/static/css/bocc.css")
up("backend/templates/dashboard.html", "backend/templates/dashboard.html")
up("backend/templates/collector.html", "backend/templates/collector.html")
up("backend/static/js/collector.js", "backend/static/js/collector.js")

sftp.close()

# Restart POCC
c.exec_command("pkill -f 'uvicorn.*backend.main' 2>/dev/null; sleep 1")
c.exec_command("cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500 > pocc.log 2>&1 </dev/null &")
time.sleep(5)

# Verify
tests = [
    ("DASHBOARD", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/"),
    ("GOVERNANCE", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/governance"),
    ("EXECUTIVE", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/executive"),
    ("RUNTIME", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/runtime"),
    ("PSEP", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/psep"),
    ("OVERVIEW_API", "curl -s http://127.0.0.1:8500/api/overview | head -c 120"),
    ("HEALTH", "curl -s http://127.0.0.1:8500/api/health | head -c 80"),
]
for label, cmd in tests:
    _, o, _ = c.exec_command(cmd)
    print(f"  {label}: {o.read().decode()[:100].strip()}")
c.close()
print("\nDone!")
