"""Deploy OSC to server and install cron."""
import paramiko, base64, time
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=10)

# Upload entire validation/osc/ directory
import os, hashlib
local_dir = r"d:\opt\pimes\pocc\validation\osc"
remote_dir = "/opt/pimes/pocc/validation/osc"

modules = [f for f in sorted(os.listdir(local_dir)) if f.endswith(".py")]
uploaded = 0
for mod in modules:
    local = os.path.join(local_dir, mod)
    b64 = base64.b64encode(open(local, "rb").read()).decode()
    with open("_up.py", "w") as f:
        f.write(f'import base64; open("{remote_dir}/{mod}","wb").write(base64.b64decode("{b64}"))')
    sftp = c.open_sftp()
    sftp.put("_up.py", "/tmp/_up.py")
    sftp.close()
    c.exec_command(f"python3 /tmp/_up.py && rm /tmp/_up.py")
    time.sleep(0.3)
    _, o, _ = c.exec_command(f"wc -c < {remote_dir}/{mod}")
    rsz = o.read().decode().strip()
    lsz = os.path.getsize(local)
    if rsz and int(rsz) == lsz:
        uploaded += 1

print(f"Uploaded {uploaded}/{len(modules)} modules")

# Create subdirs on server
for d in ["hourly", "anomalies", "baseline", "daily", "weekly", "replay"]:
    c.exec_command(f"mkdir -p {remote_dir}/data/{d} {remote_dir}/reports/{d}")
    
# Run baseline
_, o, _ = c.exec_command(f"cd /opt/pimes/pocc && /opt/pimes/laws/runtime/.venv/bin/python -m validation.osc --baseline 2>&1 | tail -3")
print(o.read().decode()[:300])

# Run one cycle
_, o, _ = c.exec_command(f"cd /opt/pimes/pocc && /opt/pimes/laws/runtime/.venv/bin/python -m validation.osc 2>&1 | tail -5")
print(o.read().decode()[:500])

# Install cron
cr = """# BOCC Operational Scientific Campaign — hourly audit
0 * * * * cd /opt/pimes/pocc && /opt/pimes/laws/runtime/.venv/bin/python -m validation.osc >> /opt/pimes/pocc/validation/osc/osc.log 2>&1
# Daily report at 00:05
5 0 * * * cd /opt/pimes/pocc && /opt/pimes/laws/runtime/.venv/bin/python -m validation.osc --daily >> /opt/pimes/pocc/validation/osc/osc_daily.log 2>&1
"""
c.exec_command(f'echo "{cr}" | crontab - 2>/dev/null; crontab -l')
_, o, _ = c.exec_command("crontab -l 2>/dev/null | head -5")
print("\nCron:", o.read().decode()[:300])

c.close()
print("\nOSC Deployed! Campaign running.")
