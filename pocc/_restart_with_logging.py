"""Fix scheduler logging and restart."""
import paramiko, base64, time, os

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

# Kill old
c.exec_command("pkill -f CollectorScheduler 2>/dev/null")
time.sleep(1)

# Upload a RUN_SCHEDULER.py that handles logging correctly
scheduler_code = """#!/usr/bin/env python3
'''Production Collector Scheduler - started manually.'''
import sys, os, logging, threading
sys.path.insert(0, "/opt/pimes/pocc")

# FORCE logging setup before anything else
import logging
logging.basicConfig(
    level=logging.INFO,
    force=True,
    format="%(asctime)s [%(name)s] %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler("/opt/pimes/laws/runtime/validation/pdac/scheduler.log"),
        logging.StreamHandler()
    ]
)

from collector.__main__ import CollectorScheduler
log = logging.getLogger("collector")

s = CollectorScheduler()
s.register("discovery", __import__("collector.discovery_worker", fromlist=["DiscoveryWorker"]).DiscoveryWorker, 300)
s.register("download", __import__("collector.download_worker", fromlist=["DownloadWorker"]).DownloadWorker, 600)
s.register("validation", __import__("collector.validation_worker", fromlist=["ValidationWorker"]).ValidationWorker, 60)
s.register("runtime", __import__("collector.runtime_trigger", fromlist=["RuntimeTriggerWorker"]).RuntimeTriggerWorker, 60)
s.register("audit", __import__("collector.audit_worker", fromlist=["AuditWorker"]).AuditWorker, 3600)

log.info("=== SCHEDULER STARTING ===")
s.start()
"""

with open("_run_scheduler.py", "w") as f:
    f.write(scheduler_code)

sftp = c.open_sftp()
sftp.put("_run_scheduler.py", "/opt/pimes/pocc/collector/_run_scheduler.py")
sftp.close()
os.remove("_run_scheduler.py")

print("Uploaded _run_scheduler.py")

# Start
c.exec_command("cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -u /opt/pimes/pocc/collector/_run_scheduler.py > /dev/null 2>&1 &")
time.sleep(5)

# Verify
_, o, _ = c.exec_command("ps aux | grep _run_scheduler | grep -v grep | head -2")
print("PROC:", o.read().decode()[:200])

_, o, _ = c.exec_command("wc -c /opt/pimes/laws/runtime/validation/pdac/scheduler.log 2>/dev/null")
print("LOG:", o.read().decode()[:100])

_, o, _ = c.exec_command("tail -20 /opt/pimes/laws/runtime/validation/pdac/scheduler.log 2>/dev/null")
print("TAIL:", o.read().decode()[:1000])

c.close()
