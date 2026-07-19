"""Upload OI module via base64."""
import paramiko, base64, os

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=10)

local = r"d:\opt\pimes\pocc\backend\operational_intelligence.py"
remote = "/opt/pimes/pocc/backend/operational_intelligence.py"

with open(local, "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

# Write upload script, upload via sftp, execute
up_script = f'import base64; open("{remote}","wb").write(base64.b64decode("{b64}"))'
with open("_up_oi.py", "w") as f:
    f.write(up_script)

sftp = c.open_sftp()
sftp.put("_up_oi.py", "/tmp/_up_oi.py")
sftp.close()

c.exec_command("python3 /tmp/_up_oi.py && rm /tmp/_up_oi.py")
import time; time.sleep(3)
os.remove("_up_oi.py")

_, o, _ = c.exec_command("wc -c < " + remote)
sz = o.read().decode().strip()
print("OI uploaded:", sz, "bytes" if sz else "FAILED!")

# Restart POCC
c.exec_command("pkill -f uvicorn 2>/dev/null; sleep 2")
c.exec_command("cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500 > pocc.log 2>&1 </dev/null &")
time.sleep(6)

# Verify
_, o, _ = c.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/api/health 2>/dev/null")
print("HEALTH:", o.read().decode().strip())
_, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/oi/health 2>/dev/null | head -c 120")
print("OI_HEALTH:", o.read().decode()[:120])

c.close()
