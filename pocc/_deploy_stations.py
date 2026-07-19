import paramiko, base64, time
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=10)

local = r"d:\opt\pimes\pocc\backend\templates\stations.html"
remote = "/opt/pimes/pocc/backend/templates/stations.html"

b64 = base64.b64encode(open(local, "rb").read()).decode()
with open("_up.py", "w") as f:
    f.write(f'import base64; open("{remote}","wb").write(base64.b64decode("{b64}"))')
sftp = c.open_sftp()
sftp.put("_up.py", "/tmp/_up.py")
sftp.close()
c.exec_command("python3 /tmp/_up.py && rm /tmp/_up.py")
time.sleep(2)

_, o, _ = c.exec_command(f"wc -c < {remote}")
print(f"Upload: {o.read().decode().strip()} bytes")

# Test
_, o, _ = c.exec_command("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/stations 2>/dev/null")
print(f"HTTP: {o.read().decode().strip()}")
c.close()
