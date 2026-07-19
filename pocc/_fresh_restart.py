import paramiko, time, os, hashlib

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=10)

# 1. Clear pycache
c.exec_command("rm -rf /opt/pimes/pocc/backend/__pycache__")
time.sleep(1)

# 2. Test import locally first
local_path = r"d:\opt\pimes\pocc\backend\infrastructure.py"
print(f"Local file: {os.path.getsize(local_path)} bytes, SHA256={hashlib.sha256(open(local_path,'rb').read()).hexdigest()[:12]}")

# 3. Verify server file
_, o, _ = c.exec_command("wc -c < /opt/pimes/pocc/backend/infrastructure.py")
remote_size = o.read().decode().strip()
print(f"Remote file: {remote_size} bytes")
assert int(remote_size) == os.path.getsize(local_path), "Size mismatch!"
print("Sizes match")

# 4. Test import on server
_, o, _ = c.exec_command("cd /opt/pimes/pocc && /opt/pimes/laws/runtime/.venv/bin/python -c 'from backend.infrastructure import pipeline_collector, sf; print(\"IMPORT OK\", sf(float(\"nan\")))' 2>&1")
import_result = o.read().decode().strip()
print(f"Import: {import_result}")

# 5. Kill existing, restart fresh
c.exec_command("pkill -f 'uvicorn.*backend.main' 2>/dev/null")
time.sleep(2)

# 6. Start fresh
c.exec_command("cat /dev/null > /opt/pimes/pocc/pocc.log && cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500 > pocc.log 2>&1 </dev/null &")
time.sleep(6)

# 7. Check health
_, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/health 2>/dev/null")
health = o.read().decode().strip()
print(f"Health: {health[:100]}")

# 8. Test pipeline API
_, o, _ = c.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/api/pipeline/stages 2>/dev/null")
pipe_code = o.read().decode().strip()
print(f"Pipeline API: HTTP {pipe_code}")

if pipe_code == "500":
    _, o, _ = c.exec_command("tail -3 /opt/pimes/pocc/pocc.log 2>/dev/null")
    print(f"Pipeline error: {o.read().decode()[:300]}")

# 9. Quick self-test
tests = ["/api/health", "/", "/engineering", "/scientific-ops", "/pipeline-runtime",
         "/alert-center", "/evidence-center", "/release-center", "/executive-center",
         "/digitaltwin", "/governance", "/api/infrastructure", "/api/pipeline/stages",
         "/api/release/status", "/api/health-model", "/api/oi/health", "/api/oi/alerts"]
p = f = 0
for t in tests:
    _, o, _ = c.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:8500{t}")
    code = o.read().decode().strip()
    ok = code in ("200", "201", "204")
    if ok: p += 1
    else: f += 1
    print(f"  {'OK' if ok else 'FAIL'} {t}: {code}")
print(f"\nSelf-test: {p}/{len(tests)} passed, {f} failed")

c.close()
