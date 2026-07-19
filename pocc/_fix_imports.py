"""Use sed to fix imports on server."""
import paramiko, time

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

_, o, _ = c.exec_command(
    "sed -i 's|from scheduler_engine import|from collector.scheduler_engine import|g' "
    "/opt/pimes/pocc/collector/discovery_worker.py "
    "/opt/pimes/pocc/collector/download_worker.py "
    "/opt/pimes/pocc/collector/validation_worker.py "
    "/opt/pimes/pocc/collector/audit_worker.py "
    "/opt/pimes/pocc/collector/runtime_trigger.py "
    "/opt/pimes/pocc/collector/scheduler_engine.py"
)
print("sed:", o.read().decode()[:200])

_, o, _ = c.exec_command("grep -n scheduler_engine /opt/pimes/pocc/collector/*.py")
print("RESULT:", o.read().decode()[:1000])

c.close()
