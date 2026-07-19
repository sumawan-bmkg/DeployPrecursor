"""Deploy RC2 dashboard — all new files via base64."""
import paramiko, base64, os, time, glob

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=10)

local_base = r"d:\opt\pimes\pocc"
files = [
    ("backend/infrastructure.py", "backend/infrastructure.py"),
    ("backend/main.py", "backend/main.py"),
    ("backend/templates/engineering.html", "backend/templates/engineering.html"),
    ("backend/templates/scientific_ops.html", "backend/templates/scientific_ops.html"),
    ("backend/templates/pipeline_runtime.html", "backend/templates/pipeline_runtime.html"),
    ("backend/templates/mission_timeline.html", "backend/templates/mission_timeline.html"),
    ("backend/templates/alert_center.html", "backend/templates/alert_center.html"),
    ("backend/templates/evidence_center.html", "backend/templates/evidence_center.html"),
    ("backend/templates/release_center.html", "backend/templates/release_center.html"),
    ("backend/templates/executive_center.html", "backend/templates/executive_center.html"),
]

def upload(local_rel, remote_rel):
    local_path = os.path.join(local_base, local_rel.replace("/", "\\"))
    remote_path = f"/opt/pimes/pocc/{remote_rel}"
    if not os.path.exists(local_path):
        print(f"  SKIP: {local_rel}")
        return
    with open(local_path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    up_script = f'import base64; open("{remote_path}","wb").write(base64.b64decode("{b64}"))'
    with open("_up_rc2.py", "w") as f:
        f.write(up_script)
    sftp = c.open_sftp()
    try:
        sftp.put("_up_rc2.py", "/tmp/_up_rc2.py")
    finally:
        sftp.close()
    c.exec_command("python3 /tmp/_up_rc2.py && rm /tmp/_up_rc2.py")
    time.sleep(0.5)
    os.remove("_up_rc2.py")
    _, o, _ = c.exec_command(f"wc -c < {remote_path}")
    sz = o.read().decode().strip()
    print(f"  {remote_rel.split('/')[-1]}: {sz} bytes" if sz else f"  {remote_rel.split('/')[-1]}: FAIL")

for local_rel, remote_rel in files:
    upload(local_rel, remote_rel)

# Restart
c.exec_command("pkill -f uvicorn 2>/dev/null; sleep 2")
c.exec_command("cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500 > pocc.log 2>&1 </dev/null &")
time.sleep(6)

# Verify
tests = [
    ("HEALTH", "curl -s http://127.0.0.1:8500/api/health|head -c 50"),
    ("ENGINEERING", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/engineering"),
    ("SCIENTIFIC_OPS", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/scientific-ops"),
    ("PIPELINE", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/pipeline-runtime"),
    ("TIMELINE", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/mission-timeline"),
    ("ALERTS", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/alert-center"),
    ("EVIDENCE", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/evidence-center"),
    ("RELEASE", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/release-center"),
    ("EXEC", "curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/executive-center"),
    ("INFRA_API", "curl -s http://127.0.0.1:8500/api/infrastructure|head -c 100"),
    ("PIPELINE_API", "curl -s http://127.0.0.1:8500/api/pipeline/stages|head -c 100"),
    ("RELEASE_API", "curl -s http://127.0.0.1:8500/api/release/status|head -c 100"),
]
print("\n=== VERIFICATION ===")
for label, cmd in tests:
    _, o, _ = c.exec_command(cmd)
    print(f"  {label}: {o.read().decode()[:100].strip()}")
c.close()
print("\nRC2 COMPLETE!")
