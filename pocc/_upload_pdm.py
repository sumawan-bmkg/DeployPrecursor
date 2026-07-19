"""Upload changed files for PDM v2.0 + restart."""
import paramiko, time
from pathlib import Path

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"

FILES = [
    (r"d:\opt\pimes\pocc\deploy.py", "/opt/pimes/pocc/deploy.py"),
    (r"d:\opt\pimes\pocc\backend\main.py", "/opt/pimes/pocc/backend/main.py"),
    (r"d:\opt\pimes\pocc\backend\templates\base.html", "/opt/pimes/pocc/backend/templates/base.html"),
    (r"d:\opt\pimes\pocc\backend\templates\deployment.html", "/opt/pimes/pocc/backend/templates/deployment.html"),
]

def main():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=10)
    sftp = c.open_sftp()
    for local, remote in FILES:
        sftp.put(local, remote)
        print(f"  {Path(local).name} OK")
    sftp.close()
    c.close()

    # Restart
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=10)
    c.exec_command("rm -rf /opt/pimes/pocc/backend/__pycache__; pkill -f 'uvicorn.*backend.main' 2>/dev/null")
    time.sleep(2)
    c.exec_command("cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500 > pocc.log 2>&1 </dev/null &")
    time.sleep(5)
    _, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/health")
    print(f"Health: {o.read().decode()[:80]}")
    c.close()

if __name__ == "__main__":
    main()
