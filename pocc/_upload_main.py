"""Upload single file via SSH base64 + restart BOCC."""
import paramiko, base64, time, sys, os
from pathlib import Path

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"
LOCAL = Path(r"d:\opt\pimes\pocc\backend\main.py")
REMOTE = "/opt/pimes/pocc/backend/main.py"

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=10)

    # Upload
    b64 = base64.b64encode(LOCAL.read_bytes()).decode()
    script = f'import base64; open("{REMOTE}","wb").write(base64.b64decode("{b64}"))'
    Path("_upload_tmp.py").write_text(script)

    sftp = c.open_sftp()
    sftp.put("_upload_tmp.py", "/tmp/_upload_tmp.py")
    sftp.close()
    _, o, _ = c.exec_command("python3 /tmp/_upload_tmp.py && rm /tmp/_upload_tmp.py")
    o.read()
    os.remove("_upload_tmp.py")

    # Verify size
    _, o, _ = c.exec_command(f"wc -c < {REMOTE}")
    remote_size = int(o.read().decode().strip())
    local_size = LOCAL.stat().st_size
    print(f"Upload: {remote_size}/{local_size} bytes {'OK' if remote_size==local_size else 'MISMATCH'}")

    # Restart
    print("Restarting...")
    c.exec_command("rm -rf /opt/pimes/pocc/backend/__pycache__")
    c.exec_command("pkill -f 'uvicorn.*backend.main' 2>/dev/null")
    time.sleep(2)
    c.exec_command("cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500 > pocc.log 2>&1 </dev/null &")
    time.sleep(4)

    # Health
    _, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/health")
    print(f"Health: {o.read().decode()[:80]}")

    c.close()

if __name__ == "__main__":
    main()
