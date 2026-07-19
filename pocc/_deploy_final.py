"""BOCC deploy — single put per file."""
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

files = [
    ("backend/main.py", "backend/main.py"),
    ("backend/static/css/bocc.css", "backend/static/css/bocc.css"),
    ("backend/templates/base.html", "backend/templates/base.html"),
    ("backend/templates/dashboard.html", "backend/templates/dashboard.html"),
    ("backend/templates/collector.html", "backend/templates/collector.html"),
    ("backend/static/js/collector.js", "backend/static/js/collector.js"),
    ("backend/governance.py", "backend/governance.py"),
    ("backend/templates/governance.html", "backend/templates/governance.html"),
]

for local_rel, remote_rel in files:
    local_path = os.path.join(LOCAL, local_rel.replace("/", "\\"))
    remote_path = f"{POCC}/{remote_rel}"
    if not os.path.exists(local_path):
        # Try artifact
        alt = rf"C:\Users\Admin\.gemini\antigravity\brain\d99cc142-5304-4d6e-9a68-187d102e1f31\scratch\{local_rel.split('/')[-1]}"
        if os.path.exists(alt): local_path = alt
        else:
            print(f"  SKIP: {local_rel}")
            continue
    try:
        sftp.put(local_path, remote_path)
        sz = sftp.stat(remote_path).st_size
        print(f"  {remote_rel.split('/')[-1]}: {sz/1000:.0f}KB")
    except Exception as e:
        print(f"  {remote_rel.split('/')[-1]}: ERR {str(e)[:40]}")

sftp.close()

# Restart
c.exec_command("pkill -f 'uvicorn.*backend.main' 2>/dev/null; sleep 2")
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
    ("COLLECTOR", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/collector"),
]
print("\n=== VERIFICATION ===")
for label, cmd in tests:
    _, o, _ = c.exec_command(cmd)
    print(f"  {label}: {o.read().decode()[:100].strip()}")
c.close()
print("\nBOCC Sprint 1 Deployed!")
