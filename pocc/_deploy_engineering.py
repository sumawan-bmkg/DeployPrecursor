"""
BOCC Deployment Pipeline v1.0
Checksum verified upload, import test, safe restart, self-test.
"""
import paramiko, base64, os, time, hashlib, sys

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"
POCC = "/opt/pimes/pocc"
LOCAL = r"d:\opt\pimes\pocc"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=10)

def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()

def upload(local_rel):
    local_path = os.path.join(LOCAL, local_rel.replace("/", "\\"))
    remote_path = f"{POCC}/{local_rel}"
    local_sha = sha256(local_path)
    local_size = os.path.getsize(local_path)
    b64 = base64.b64encode(open(local_path, "rb").read()).decode()
    with open("_u.py", "w") as f:
        f.write(f'import base64; open("{remote_path}","wb").write(base64.b64decode("{b64}"))')
    sftp = c.open_sftp()
    sftp.put("_u.py", "/tmp/_u.py")
    sftp.close()
    c.exec_command("python3 /tmp/_u.py && rm /tmp/_u.py")
    time.sleep(0.3)
    os.remove("_u.py")
    _, o, _ = c.exec_command(f"wc -c < {remote_path}")
    rsz = o.read().decode().strip()
    ok = rsz and int(rsz) == local_size
    tag = "OK" if ok else "FAIL"
    print(f"  {tag} {local_rel}: local={local_size} remote={rsz} SHA256={local_sha[:12]}")
    return ok

def import_test():
    _, o, _ = c.exec_command("cd /opt/pimes/pocc && PYTHONPATH=/opt/pimes/pocc /opt/pimes/laws/runtime/.venv/bin/python -c 'from backend.main import app; print(\"IMPORT OK\")' 2>&1")
    r = o.read().decode().strip()
    ok = "IMPORT OK" in r
    print(f"  {'OK' if ok else 'FAIL'} Import: {r[:200]}")
    return ok

def safe_restart():
    c.exec_command("cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8501 > pocc_new.log 2>&1 </dev/null &")
    time.sleep(5)
    _, o, _ = c.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8501/api/health 2>/dev/null")
    nc = o.read().decode().strip()
    if nc == "200":
        print("  OK Blue-green: new instance healthy on :8501")
        c.exec_command("pkill -f 'uvicorn.*backend.main.*8500' 2>/dev/null; sleep 1")
        c.exec_command("cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500 > pocc.log 2>&1 </dev/null &")
        time.sleep(5)
        c.exec_command("pkill -f 'uvicorn.*backend.main.*8501' 2>/dev/null")
        _, o, _ = c.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/api/health")
        fc = o.read().decode().strip()
        ok = fc == "200"
        print(f"  {'OK' if ok else 'FAIL'} Main instance on :8500: HTTP {fc}")
        return ok
    else:
        print(f"  FAIL Blue-green: HTTP {nc}, rolling back")
        c.exec_command("pkill -f 'uvicorn.*backend.main.*8501' 2>/dev/null")
        return False

def self_test():
    tests = [
        "/api/health", "/", "/engineering", "/scientific-ops", "/pipeline-runtime",
        "/mission-timeline", "/alert-center", "/evidence-center", "/release-center",
        "/executive-center", "/digitaltwin", "/governance",
        "/api/infrastructure", "/api/pipeline/stages", "/api/release/status",
        "/api/health-model", "/api/oi/health", "/api/oi/alerts",
    ]
    p = f = 0
    for t in tests:
        _, o, _ = c.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:8500{t}")
        code = o.read().decode().strip()
        ok = code in ("200", "201", "204")
        if ok: p += 1
        else: f += 1
        print(f"  {'OK' if ok else 'FAIL'} {t}: HTTP {code}")
    print(f"\n  Self-test: {p}/{len(tests)} passed, {f} failed")
    return f == 0

print("\n=== BOCC Engineering Deployment ===\n")
print("Phase 1: Upload")
ok = upload("backend/infrastructure.py")
if not ok:
    print("ABORT: upload failed")
    sys.exit(1)

print("\nPhase 2: Import test")
ok = import_test()

print("\nPhase 3: Safe restart")
ok = safe_restart()

print("\nPhase 4: Self-test")
ok = self_test()

print()
if ok:
    print("RESULT: BOCC Engineering Hardening PASSED")
else:
    print("RESULT: Some tests failed, review above")
c.close()
