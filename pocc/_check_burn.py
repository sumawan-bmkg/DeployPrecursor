import paramiko, json
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=10)

# Burn-in status
_, o, _ = c.exec_command("cat /opt/pimes/laws/runtime/validation/burnin/burnin_status.json")
print("BURNIN_STATUS:", o.read().decode()[:500])

_, o, _ = c.exec_command("cat /opt/pimes/laws/runtime/validation/burnin/burnin_log.csv | tail -5")
print("BURNIN_LOG:", o.read().decode()[:500])

_, o, _ = c.exec_command("cat /opt/pimes/laws/runtime/validation/burnin/BURNIN_REPORT.md | head -30")
print("BURNIN_REPORT:", o.read().decode()[:500])

_, o, _ = c.exec_command("ps aux | grep -i burn | grep -v grep")
print("BURN_PROC:", o.read().decode()[:200])

_, o, _ = c.exec_command("ls -la /opt/pimes/laws/runtime/validation/burnin/")
print("BURNIN_LS:", o.read().decode()[:500])

_, o, _ = c.exec_command("cat /opt/pimes/laws/runtime/validation/psep/dual_execution/runs/ 2>/dev/null; ls /opt/pimes/laws/runtime/validation/psep/dual_execution/runs/ 2>/dev/null")
print("PSEP_RUNS:", o.read().decode()[:300])

c.close()
