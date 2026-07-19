"""ODDQ Phase 1-2: Full storage discovery + waveform inventory."""
import paramiko, json, hashlib
from datetime import datetime

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=10)

def run(cmd):
    _, o, _ = c.exec_command(cmd)
    return o.read().decode().strip()

print("=" * 60)
print("ODDQ — PHASE 1 & 2: STORAGE DISCOVERY + WAVEFORM INVENTORY")
print("=" * 60)

# Phase 1: Storage discovery
print("\n--- STORAGE DISCOVERY ---")
storage_paths = [
    "/opt/pimes/data", "/opt/pimes/laws", "/opt/pimes/laws/h5",
    "/opt/pimes/laws/runtime", "/opt/pimes/laws/priors",
    "/opt/pimes/pocc", "/opt/pimes/posc",
    "/opt/pimes/shadow_v95", "/opt/pimes/backup",
    "/opt/pimes/repository", "/opt/pimes/archive",
    "/opt/pimes/raw", "/mnt",
]
for p in storage_paths:
    exists = run(f"test -d {p} && echo YES || echo NO")
    sz = run(f"du -sh {p} 2>/dev/null | cut -f1") if exists == "YES" else "–"
    files = run(f"find {p} -type f 2>/dev/null | wc -l") if exists == "YES" else "–"
    print(f"  {p:<40} {'EXISTS' if exists=='YES' else 'MISS':>6}  {sz:>8}  {files:>6} files")

# Phase 2: Waveform inventory
print("\n--- WAVEFORM INVENTORY ---")
extensions_to_find = "*.h5 *.hdf5 *.bin *.mseed *.miniseed *.sac *.segy *.npy *.csv *.txt"
all_waveform = run(f"find /opt/pimes -type f \\( -name '*.h5' -o -name '*.hdf5' -o -name '*.bin' -o -name '*.mseed' -o -name '*.sac' -o -name '*.segy' -o -name '*.npy' \\) 2>/dev/null | head -200")
ext_summary = run("for ext in h5 hdf5 bin mseed sac segy npy csv txt; do c=$(find /opt/pimes -name '*.'$ext 2>/dev/null | wc -l); echo \"$ext: $c files\"; done")
print(ext_summary)

print("\n--- ALL DATA FILES BY EXTENSION ---")
all_ext = run("find /opt/pimes -type f 2>/dev/null | sed 's/.*\\.//' | sort | uniq -c | sort -rn | head -30")
print(all_ext)

# Phase 3: Station mapping
print("\n--- STATION MAPPING ---")
# Raw data dirs
raw_dirs = run("ls -d /opt/pimes/data/raw/*/ 2>/dev/null | sed 's|.*/||' | tr '\n' ' '")
print(f"  Raw data dirs: {raw_dirs}")

# Priors
priors = run("find /opt/pimes/laws/priors -name '*.pt' 2>/dev/null | sed 's/.*prior_//' | sed 's/.pt$//' | sort | tr '\n' ' '")
print(f"  Priors (.pt): {priors}")

# Signatures
sigs = run("ls /opt/pimes/laws/runtime/validation/rdmc/artifacts/station_*_signature.json 2>/dev/null | sed 's/.*station_//' | sed 's/_signature.json//' | sort | tr '\n' ' '")
print(f"  Signatures:   {sigs}")

# Sample raw data per station
print("\n--- RAW DATA SAMPLE PER STATION ---")
stations = run("ls -d /opt/pimes/data/raw/*/ 2>/dev/null | sed 's|.*/||'").split()
for s in sorted(stations)[:15]:
    cnt = run(f"find /opt/pimes/data/raw/{s} -type f 2>/dev/null | wc -l")
    sz = run(f"du -sh /opt/pimes/data/raw/{s} 2>/dev/null | cut -f1")
    ext = run(f"find /opt/pimes/data/raw/{s} -type f 2>/dev/null | sed 's/.*\\.//' | sort -u | tr '\\n' ' '")
    ts = run(f"ls -t /opt/pimes/data/raw/{s} 2>/dev/null | tail -1")
    print(f"  {s:<10} {sz:>6}  {cnt:>5} files  [{ext[:50]}]  latest: {ts[:30]}")

# Phase 4: Collector log audit
print("\n--- COLLECTOR LOG AUDIT ---")
clog = run("tail -50 /opt/pimes/logs/collector/collector.log 2>/dev/null")
print(clog[:1000] if clog else "  (empty)")

# Phase 5: Total data sizes
print("\n--- TOTAL DATA SIZES ---")
sizes = run("du -sh /opt/pimes/data/*/ 2>/dev/null | sort -rh")
print(sizes)

c.close()
