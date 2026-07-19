"""Audit raw data counts + collector logs + station coverage."""
import paramiko

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=10)

checks = {
    "RAW_STATION_COUNT": "ls -d /opt/pimes/data/raw/*/ 2>/dev/null | wc -l",
    "RAW_FILES_TOTAL": "find /opt/pimes/data/raw -type f -name '*.h5' -o -name '*.npy' -o -name '*.csv' -o -name '*.bin' 2>/dev/null | wc -l",
    "RAW_ALL_FILES": "find /opt/pimes/data/raw -type f 2>/dev/null | wc -l",
    "TENSOR_COUNT": "find /opt/pimes/data/tensors -type f 2>/dev/null | wc -l",
    "SCALOGRAM_COUNT": "find /opt/pimes/data/scalogram -type f 2>/dev/null | wc -l",
    "PREDICTION_COUNT": "find /opt/pimes/data/predictions -type f 2>/dev/null | wc -l",
    "STATION_DIRS": "ls /opt/pimes/data/raw/ 2>/dev/null",
    "RAW_EXTENSIONS": "find /opt/pimes/data/raw -type f 2>/dev/null | sed 's/.*\\.//' | sort | uniq -c | sort -rn | head -10",
    "PREDICTION_SAMPLES": "find /opt/pimes/data/predictions -type f 2>/dev/null | head -10",
    "TENSOR_SAMPLES": "find /opt/pimes/data/tensors -type f 2>/dev/null | head -10",
    "SCALOGRAM_SAMPLES": "find /opt/pimes/data/scalogram -type f 2>/dev/null | head -10",
    "COLLECTOR_LOG_TAIL": "tail -30 /opt/pimes/logs/collector/collector.log 2>/dev/null",
    "COLLECTOR_SCHEDULER": "tail -30 /opt/pimes/laws/runtime/validation/pdac/scheduler.log 2>/dev/null",
    "GOLDEN_DATASET": "ls /opt/pimes/laws/runtime/validation/golden_dataset/ 2>/dev/null",
    "BURNIN_CYCLES": "ls /opt/pimes/laws/runtime/validation/burnin/ 2>/dev/null",
    "PRIOR_PT_COUNT": "find /opt/pimes/laws/priors -name '*.pt' 2>/dev/null | wc -l",
    "PRIOR_METADATA_COUNT": "find /opt/pimes/laws/priors -name '*.txt' 2>/dev/null | wc -l",
    "PRIOR_STATIONS": "find /opt/pimes/laws/priors -name '*.pt' 2>/dev/null | sed 's/.*prior_//' | sed 's/.pt$//' | sort",
    "H5_STATIONS": "find /opt/pimes/laws/h5 -name '*.h5' 2>/dev/null | sed 's/.*scalogram_//' | sed 's/_[0-9].*$//'",
}

for name, cmd_str in checks.items():
    _, o, _ = c.exec_command(cmd_str)
    out = o.read().decode().strip()
    print(f"\n--- {name} ---")
    if out:
        for l in out.split('\n')[:40]:
            print(f"  {l}")
    else:
        print("  (empty)")

c.close()
