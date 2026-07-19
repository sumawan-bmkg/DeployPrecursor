"""BOCC Governance Layer — one-shot deploy.
Deploys: governance.py, governance.html, main.py (updated), collector.js, collector.html
"""
import paramiko, base64, os, time, json

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"
POCC = "/opt/pimes/pocc"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())

# Wait for server
print("Waiting for server...")
for i in range(30):
    try:
        c.connect(HOST, username=USER, password=PASS, timeout=5)
        print("Connected!")
        break
    except:
        time.sleep(10)
else:
    print("Server still unreachable. Files ready. Will retry.")
    c.close()
    exit(1)

files = {
    "backend/governance.py": r"d:\opt\pimes\pocc\backend\governance.py",
    "backend/templates/governance.html": r"d:\opt\pimes\pocc\backend\templates\governance.html",  # will be deployed via content
    "backend/main.py": r"d:\opt\pimes\pocc\backend\main.py",
}

# Upload governance.py
for rel, local in files.items():
    if not os.path.exists(local):
        # governance.html doesn't exist locally, create from the scratch file
        if "governance.html" in rel:
            scratch = r"C:\Users\Admin\.gemini\antigravity\brain\d99cc142-5304-4d6e-9a68-187d102e1f31\scratch\governance.html"
            if os.path.exists(scratch):
                with open(scratch, "rb") as f:
                    data = base64.b64encode(f.read()).decode()
                remote = f"{POCC}/{rel}"
                script = f'import base64; open("{remote}","wb").write(base64.b64decode("{data}"))'
                with open("_tmp_up.py", "w") as f:
                    f.write(script)
                sftp = c.open_sftp()
                sftp.put("_tmp_up.py", "/tmp/_up.py")
                sftp.close()
                c.exec_command("python3 /tmp/_up.py && rm /tmp/_up.py")
                time.sleep(0.3)
                os.remove("_tmp_up.py")
                _, o, _ = c.exec_command(f"wc -c < {remote}")
                print(f"  governance.html: {o.read().decode().strip()} bytes")
            continue
        print(f"SKIP: {local}")
        continue
    remote = f"{POCC}/{rel}"
    with open(local, "rb") as f:
        data = base64.b64encode(f.read()).decode()
    script = f'import base64; open("{remote}","wb").write(base64.b64decode("{data}"))'
    with open("_tmp_up.py", "w") as f:
        f.write(script)
    sftp = c.open_sftp()
    sftp.put("_tmp_up.py", "/tmp/_up.py")
    sftp.close()
    c.exec_command("python3 /tmp/_up.py && rm /tmp/_up.py")
    time.sleep(0.3)
    os.remove("_tmp_up.py")
    _, o, _ = c.exec_command(f"wc -c < {remote}")
    print(f"  {rel.split('/')[-1]}: {o.read().decode().strip()} bytes")

# Kill old POCC
c.exec_command("pkill -f 'uvicorn.*backend.main' 2>/dev/null; sleep 1")

# Start new POCC
c.exec_command("cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500 > /opt/pimes/pocc/pocc.log 2>&1 </dev/null &")
time.sleep(5)

# Test all endpoints
tests = {
    "HEALTH": "curl -s http://127.0.0.1:8500/api/health | head -c 100",
    "GOV_ROLES": "curl -s http://127.0.0.1:8500/api/governance/roles | head -c 200",
    "GOV_STATES": "curl -s http://127.0.0.1:8500/api/governance/states | head -c 200",
    "CONTROL_LIST": "curl -s http://127.0.0.1:8500/api/control/list?limit=5 | head -c 200",
    "CONTROL_REQ": "curl -s -X POST http://127.0.0.1:8500/api/control/request -H 'Content-Type: application/json' -d '{\"action\":\"discover\",\"operator\":\"deploy\"}'",
    "GOOGLE_PAGE": "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/governance",
    "COLLECTOR_PAGE": "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/collector",
}
print("\n=== VERIFICATION ===")
for label, cmd in tests.items():
    _, o, _ = c.exec_command(cmd)
    out = o.read().decode("utf-8", "replace")[:300]
    print(f"  {label}: {out.strip()[:100]}")

c.close()
print("\nDeployment complete.")
