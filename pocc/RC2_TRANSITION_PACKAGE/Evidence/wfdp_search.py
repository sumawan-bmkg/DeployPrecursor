"""WFDP Phase 1-3: Full filesystem waveform discovery."""
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
print("WFDP: WAVEFORM DATASET DISCOVERY PROGRAM")
print("=" * 60)

# Phase 1: Search ALL data files across filesystem
print("\n\n=== PHASE 1: FILESYSTEM WIDE DATA FILE SEARCH ===")
extensions = ["lem", "dat", "bin", "raw", "txt", "csv", "h5", "hdf5", "npy", "mseed", "sac", "seed", "zip", "gz", "tar"]

for ext in extensions:
    cmd_str = f"find /opt /mnt /data /tmp -name '*.{ext}' -type f 2>/dev/null | wc -l"
    count = run(cmd_str)
    sz_cmd = f"find /opt /mnt /data /tmp -name '*.{ext}' -type f -exec stat --format='%s' {{}} + 2>/dev/null | awk '{{s+=$1}}END{{print s}}'"
    total_bytes = run(sz_cmd)
    size_str = "?"
    try:
        total = int(total_bytes)
        if total > 1073741824:
            size_str = f"{total/1073741824:.1f}GB"
        elif total > 1048576:
            size_str = f"{total/1048576:.1f}MB"
        elif total > 1024:
            size_str = f"{total/1024:.1f}KB"
        else:
            size_str = f"{total}B"
    except:
        pass
    if count and count != "0":
        print(f"  *.{ext:<8} {count:>6} files  {size_str:>10}")

# Phase 2: Find ALL data files (excluding Python/Jupyter/compiled)
print("\n\n=== PHASE 2: RECENT FILES (modified 2025-2026) ===")
recent = run("find /opt /mnt -type f \\( -name '*.h5' -o -name '*.lem' -o -name '*.bin' -o -name '*.raw' -o -name '*.dat' -o -name '*.npy' -o -name '*.mseed' -o -name '*.sac' -o -name '*.tar.gz' -o -name '*.zip' \\) -newermt '2025-01-01' 2>/dev/null | head -100")
for line in recent.split("\n"):
    if line.strip():
        sz = run(f"stat --format='%s %y' {line} 2>/dev/null")
        print(f"  {sz:<50} {line}")

# Phase 3: Search for any file modified 2025-01-01 onward (non-pyc, non-cache)
print("\n\n=== PHASE 3: ANY NON-CODE FILES MODIFIED 2025-2026 ===")
all_non_code = run("find /opt -type f -newermt '2025-01-01' ! -name '*.py' ! -name '*.pyc' ! -name '*.js' ! -name '*.css' ! -path '*/.venv/*' ! -path '*/__pycache__/*' ! -path '*/node_modules/*' 2>/dev/null | wc -l")
print(f"  Total non-code files: {all_non_code}")

# Most interesting large files
large = run("find /opt -type f -size +10M -newermt '2025-01-01' ! -name '*.pyc' ! -path '*/.venv/*' 2>/dev/null | head -30")
print(f"\n  Large files (>10MB, modified 2025+):")
for line in large.split("\n"):
    if line.strip():
        sz_time = run(f"stat --format='%s %y' {line} 2>/dev/null")
        print(f"    {sz_time:<55} {line}")

# Check /opt/pimes/laws/h5 and data dirs
print("\n\n=== PHASE 4: H5 FILES ===")
all_h5 = run("find /opt -name '*.h5' -exec ls -la {} \\; 2>/dev/null")
for line in all_h5.split("\n"):
    if line.strip(): print(f"  {line}")

# Check scalogram/data dirs
print("\n\n=== PHASE 5: SCALOGRAM CACHE ===")
scal = run("find /opt -path '*scalogram*' -type f 2>/dev/null | head -20")
for line in scal.split("\n"):
    if line.strip():
        sz_time = run(f"stat --format='%s %y' {line} 2>/dev/null")
        print(f"  {sz_time:<55} {line}")

# Check runtime data/output
print("\n\n=== PHASE 6: RUNTIME DATA CACHE ===")
rt_data = run("find /opt/pimes/laws/runtime -type f -size +1M ! -name '*.py' ! -name '*.pyc' 2>/dev/null | head -30")
for line in rt_data.split("\n"):
    if line.strip():
        sz = run(f"stat --format='%s %y' {line} 2>/dev/null")
        print(f"  {sz:<55} {line}")

# Collector output files
print("\n\n=== PHASE 7: COLLECTOR CACHE ===")
col_data = run("find /opt -path '*collector*' -type f -newermt '2025-01-01' ! -name '*.py' 2>/dev/null | head -20")
for line in col_data.split("\n"):
    if line.strip():
        print(f"  {line}")

# Check /opt/pimes/data recursively
print("\n\n=== PHASE 8: /opt/pimes/data FULL TREE ===")
data_tree = run("find /opt/pimes/data -type f 2>/dev/null | head -50")
for line in data_tree.split("\n"):
    if line.strip():
        sz = run(f"stat --format='%s %y %n' {line} 2>/dev/null")
        print(f"  {sz}")

# Mount points
print("\n\n=== PHASE 9: MOUNTS ===")
mounts = run("mount | grep -E 'nfs|cifs|fuse|ext' | grep -v proc | head -20")
print(mounts[:1000])

# df -h for all
print("\n\n=== PHASE 10: DISK USAGE ===")
disks = run("df -h | head -30")
print(disks)

c.close()
