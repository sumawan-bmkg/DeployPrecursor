"""Server data audit — find all data sources available for blind test."""
import paramiko

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=10)

checks = {
    "ULF_DATA": "find /opt/pimes -name '*.mseed' -o -name '*.miniseed' -o -name '*.sac' -o -name '*.segy' -o -name '*.h5' -o -name '*.hdf5' 2>/dev/null | head -20",
    "STATION_LISTS": "find /opt/pimes -name '*station*' -o -name '*channel*' -o -name '*sensor*' -o -name '*stasiun*' 2>/dev/null | head -10",
    "COLLECTOR_DATA": "ls /opt/pimes/pocc/collector/ 2>/dev/null; find /opt/pimes/pocc/collector -type f 2>/dev/null | head -10",
    "POSC_STRUCTURE": "find /opt/pimes/posc -maxdepth 3 -type d 2>/dev/null",
    "PIMES_DATA_DIRS": "find /opt/pimes -maxdepth 2 -name 'data' -type d 2>/dev/null",
    "RAW_DATA_SEARCH": "find /opt -maxdepth 4 -name '*.txt' -path '*/pimes/*' -o -name '*.bin' -path '*/pimes/*' 2>/dev/null | head -20",
    "HOURGLASS_DATA": "ls /opt/pimes/laws/runtime/data/ 2>/dev/null | head -20",
    "PDAC_DATA": "find /opt/pimes/pdac -maxdepth 3 -type d 2>/dev/null | head -10",
    "COLLECTOR_WORKERS": "ps aux | grep '[c]ollector' 2>/dev/null || echo NO_COLLECTOR_PROC",
    "RDMC_ARTIFACTS": "ls /opt/pimes/laws/runtime/validation/rdmc/artifacts/ 2>/dev/null | head -10",
    "BURNIN_DATA": "ls /opt/pimes/laws/runtime/validation/burnin/data/ 2>/dev/null | head -10",
    "CSQ_DATA": "ls /opt/pimes/posc/csq/data/ 2>/dev/null | head -10",
    "SEOS_DATA": "ls /opt/pimes/pocc/validation/seos/evidence_db/ 2>/dev/null | head -10",
    "OSRV_REPORTS": "ls /opt/pimes/pocc/validation/osrv/reports/ 2>/dev/null | head -10",
}

for name, cmd_str in checks.items():
    _, o, _ = c.exec_command(cmd_str)
    out = o.read().decode().strip()
    lines = out.split('\n') if out else []
    print(f"\n{'='*50}")
    print(f"  {name}")
    print(f"{'='*50}")
    for l in lines[:15]:
        print(f"  {l}")
    if not out:
        print("  (empty)")

c.close()
