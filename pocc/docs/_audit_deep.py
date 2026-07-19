"""Deep audit — waveform data, station coverage, collector logs."""
import paramiko

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=10)

checks = {
    "H5_FILES_TOTAL": "find /opt/pimes/laws/h5 -name '*.h5' | wc -l",
    "H5_FILE_LIST": "find /opt/pimes/laws/h5 -name '*.h5' -exec ls -lh {} \\; 2>/dev/null",
    "STATION_SIGNATURES": "ls /opt/pimes/laws/runtime/validation/rdmc/artifacts/station_*_signature.json 2>/dev/null | wc -l",
    "STATION_NAMES": "ls /opt/pimes/laws/runtime/validation/rdmc/artifacts/station_*_signature.json 2>/dev/null | sed 's/.*station_//' | sed 's/_signature.json//'",
    "COLLECTOR_QUEUE": "find /opt/pimes/pocc/collector -name '*.py' -exec grep -l 'queue\|session\|download\|scheduler' {} \\; 2>/dev/null | head -5",
    "COLLECTOR_LOG": "find /opt -name 'collector*.log' -o -name 'scheduler*.log' 2>/dev/null | head -5",
    "RAW_DATA_STATIONS": "ls /opt/pimes/data/ 2>/dev/null | head -30",
    "DATA_FOLDER": "find /opt/pimes/data -maxdepth 2 -type d 2>/dev/null | head -30",
    "PRIOR_STATIONS": "ls /opt/pimes/laws/priors/ 2>/dev/null | grep -v __pycache__ | head -30",
    "COLLECTOR_LOG_CONTENT": "find /opt/pimes -name 'scheduler.log' -o -name 'collector.log' 2>/dev/null | head -3",
    "RDMC_ARTIFACTS_LIST": "ls /opt/pimes/laws/runtime/validation/rdmc/artifacts/ 2>/dev/null",
    "TOTAL_DATA_SIZE": "du -sh /opt/pimes/laws/h5/ 2>/dev/null",
    "COLLECTOR_RUN_FILES": "find /opt/pimes/pocc/collector -name '*.py' -exec echo {} \\;",
    "PIPELINE_RESULTS": "find /opt/pimes/laws/runtime -name 'prediction*' -o -name 'tensor*' -o -name 'inference*' 2>/dev/null | head -10",
    "PC3_DATA": "find /opt/pimes -name 'pc3*' -o -name 'PC3*' -o -name 'cwt*' 2>/dev/null | head -10",
    "INFERENCE_DATA": "find /opt/pimes -path '*/inference/*' -name '*.npy' -o -path '*/inference/*' -name '*.pt' 2>/dev/null | head -10",
}

for name, cmd_str in checks.items():
    _, o, _ = c.exec_command(cmd_str)
    out = o.read().decode().strip()
    lines = out.split('\n') if out else []
    print(f"\n--- {name} ---")
    for l in lines[:30]:
        print(f"  {l}")
    if not out:
        print("  (empty)")

c.close()
