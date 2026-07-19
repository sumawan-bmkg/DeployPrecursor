"""ODDQ Phase 3: Per-station raw data audit + .npy analysis."""
import paramiko

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
print("ODDQ PHASE 3: RAW DATA PER STATION + .NPY ANALYSIS")
print("=" * 60)

# Per-station raw breakdown
print("\n--- PER-STATION RAW DATA (509MB total) ---")
print("  (sorted by size)")
st_results = run("du -sh /opt/pimes/data/raw/*/ 2>/dev/null | sort -rh | head -50")
for line in st_results.split("\n"):
    parts = line.strip().split()
    if len(parts) >= 2:
        sz = parts[0]
        path = parts[1]
        station = path.rstrip("/").split("/")[-1]
        fcount = run(f"find {path} -type f 2>/dev/null | wc -l")
        exts = run(f"find {path} -type f 2>/dev/null | sed 's/.*\\.//' | sort -u | tr '\\n' ' '")
        # Check for time range
        oldest = run(f"ls -t {path} 2>/dev/null | tail -1")
        newest = run(f"ls -t {path} 2>/dev/null | head -1")
        print(f"  {station:<10} {sz:>6}  {fcount:>5} files  [{exts[:40]}]  oldest: {oldest[:25]} newest: {newest[:25]}")

# .npy files audit
print("\n--- .NPY FILES (108 total) ---")
print("  (these are likely tensors/features)")
npy_locations = run("find /opt/pimes -name '*.npy' 2>/dev/null | head -50")
print(npy_locations)

# .mat files audit (Matlab — could be raw waveform!)
print("\n--- .MAT FILES (111 total) ---")
mat_locations = run("find /opt/pimes -name '*.mat' 2>/dev/null | head -30")
print(mat_locations)

# Repository contents
print("\n--- REPOSITORY (37MB) ---")
repo = run("ls -la /opt/pimes/repository/ 2>/dev/null")
print(repo[:1000])

# H5 deep scan
print("\n--- H5 DEEP SCAN ---")
h5_all = run("find /opt/pimes -name '*.h5' -exec ls -lh {} \\; 2>/dev/null")
print(h5_all)

# .csv files that could be time series
print("\n--- CSV FILES (66 total) ---")
csv_all = run("find /opt/pimes -name '*.csv' -type f 2>/dev/null | head -30")
print(csv_all)

# archive dirs
print("\n--- ARCHIVE CONTENTS ---")
arch = run("find /opt/pimes/data/archive -type f 2>/dev/null | head -10")
print(arch if arch else "  (empty)")

print("\n--- RAW/ARCHIVE ---")
raw_arch = run("find /opt/pimes/data/raw/archive -type f 2>/dev/null | head -10")
print(raw_arch if raw_arch else "  (empty)")

# Prior .pt files details
print("\n--- PRIOR .PT FILES ---")
pt_all = run("find /opt/pimes/laws/priors -name '*.pt' 2>/dev/null")
print(pt_all)

# Collector last activity
print("\n--- COLLECTOR ACTIVITY ---")
print(run("tail -10 /opt/pimes/logs/collector/collector.log 2>/dev/null"))
print()
print(run("tail -10 /opt/pimes/laws/runtime/validation/pdac/scheduler.log 2>/dev/null"))

c.close()
