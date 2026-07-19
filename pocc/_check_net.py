"""Check server connectivity."""
import paramiko, socket, time

host = "10.20.229.43"

# Quick TCP check
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.settimeout(3)
try:
    s.connect((host, 22))
    print("Port 22: OPEN")
    s.close()
except Exception as e:
    print("Port 22:", str(e)[:80])

# SSH check
try:
    c = paramiko.SSHClient()
    c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(host, username="bmkg", password="precursor@admin2026!", timeout=10)
    print("SSH: CONNECTED")
    _, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/health")
    print("POCC:", o.read().decode()[:200])
    c.close()
except Exception as e:
    print("SSH:", str(e)[:100])
