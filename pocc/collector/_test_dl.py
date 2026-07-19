import paramiko, base64, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

# Run download worker
script = """import sys
sys.path.insert(0, "/opt/pimes/pocc/collector")
from download_worker import DownloadWorker
from scheduler_engine import manifest

print("IMPORT OK")
w = DownloadWorker("download_test", manifest, interval=1)
try:
    r = w.execute()
    print("RESULT:", r)
except Exception as e:
    print("FAIL:", str(e)[:300])
"""

with open("d:/opt/pimes/pocc/collector/_test_download.py", "w") as f:
    f.write(script)

with open("d:/opt/pimes/pocc/collector/_test_download.py", "rb") as f:
    data = base64.b64encode(f.read()).decode()

c.exec_command("python3 -c \"import base64; open('/opt/pimes/pocc/collector/_test_download.py','wb').write(base64.b64decode('%s'))\"" % data)
time.sleep(1)

_, o, _ = c.exec_command("PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/opt/pimes/pocc/collector /opt/pimes/laws/runtime/.venv/bin/python3 /opt/pimes/pocc/collector/_test_download.py 2>&1")
output = o.read().decode()[:3000]
print("OUTPUT:", output)

# Check download queue
_, o, _ = c.exec_command("cat /opt/pimes/laws/runtime/validation/pdac/download_queue.json 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);print(json.dumps(d.get(\"stats\",{})))' 2>/dev/null")
print("QUEUE STATS:", o.read().decode()[:200])
c.close()
