"""Fast deploy — SFTP upload + restart."""
import paramiko, time, os
from pathlib import Path

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"
LOCAL = Path(r"d:\opt\pimes\pocc")

def ssh():
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, password=PASS, timeout=10)
    return c

def cmd(c, command):
    _, o, _ = c.exec_command(command)
    return o.read().decode().strip()

def upload_file(local, remote):
    """Upload one file via SFTP."""
    c = ssh()
    sftp = c.open_sftp()
    try:
        sftp.put(str(local), str(remote))
        ok = True
    except Exception as e:
        print(f"  FAIL: {local.name} ({e})")
        ok = False
    sftp.close()
    c.close()
    return ok

def deploy():
    print("\n=== DEPLOY ===\n")

    # Step 1: Upload main.py
    print("[1/3] Uploading backend/main.py...")
    upload_file(LOCAL / "backend" / "main.py", "/opt/pimes/pocc/backend/main.py")

    # Step 2: Upload all templates
    print("[2/3] Uploading templates...")
    ok = 0
    fail = 0
    tmpl = LOCAL / "backend" / "templates"
    c = ssh()
    sftp = c.open_sftp()
    for f in sorted(tmpl.glob("*.html")):
        try:
            sftp.put(str(f), f"/opt/pimes/pocc/backend/templates/{f.name}")
            ok += 1
        except:
            fail += 1
    sftp.close()
    c.close()
    print(f"  {ok} uploaded, {fail} failed")

    # Step 3: Restart
    print("[3/3] Restarting BOCC...")
    c = ssh()
    cmd(c, "rm -rf /opt/pimes/pocc/backend/__pycache__")
    cmd(c, "pkill -f 'uvicorn.*backend.main' 2>/dev/null; sleep 2")
    cmd(c, "cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8500 > pocc.log 2>&1 </dev/null &")
    time.sleep(5)
    health = cmd(c, "curl -s http://127.0.0.1:8500/api/health | head -c 60")
    print(f"  Health: {health}")
    c.close()
    print("\n=== DONE ===")

if __name__ == "__main__":
    deploy()
