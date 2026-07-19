import paramiko, base64, time, os
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=10)
local_path = r"d:\opt\pimes\pocc\backend\infrastructure.py"
remote_path = "/opt/pimes/pocc/backend/infrastructure.py"
local_size = os.path.getsize(local_path)
b64 = base64.b64encode(open(local_path, "rb").read()).decode()
with open("_up.py", "w") as f:
    f.write(f'import base64; open("{remote_path}","wb").write(base64.b64decode("{b64}"))')
sftp = c.open_sftp()
sftp.put("_up.py", "/tmp/_up.py")
sftp.close()
c.exec_command("python3 /tmp/_up.py && rm /tmp/_up.py")
time.sleep(2)
os.remove("_up.py")
_, o, _ = c.exec_command(f"wc -c < {remote_path}")
rsz = o.read().decode().strip()
print(f"Upload: local={local_size} remote={rsz} {'OK' if rsz and int(rsz)==local_size else 'FAIL'}")
# Clear cache and restart
c.exec_command("rm -rf /opt/pimes/pocc/backend/__pycache__; pkill -f 'uvicorn.*backend.main' 2>/dev/null; sleep 2")
c.exec_command("cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500 > pocc.log 2>&1 </dev/null &")
time.sleep(6)
_, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/pipeline/stages 2>/dev/null | head -c 150")
print(f"Pipeline: {o.read().decode()[:200]}")
_, o, _ = c.exec_command("tail -5 /opt/pimes/pocc/pocc.log 2>/dev/null")
print(f"Log: {o.read().decode()[:300]}")
c.close()
