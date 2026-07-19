"""LFCP Phase 1-2: LEM File Inventory + Binary Characterization."""
import paramiko, hashlib

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
print("LFCP PHASE 1: LEM FILE INVENTORY")
print("=" * 60)

# Phase 1: Complete inventory
print("\n--- ALL .LEM FILES ---")
lem_files = run("find /opt/pimes/data/raw -name '*.lem' -exec ls -la {} \\; 2>/dev/null")
print(lem_files)

print("\n--- FILE COUNT PER STATION ---")
print(run("find /opt/pimes/data/raw -name '*.lem' | sed 's|/opt/pimes/data/raw/||' | sed 's|/.*||' | sort | uniq -c | sort -rn"))

print("\n--- TOTAL LEM FILES ---")
print(run("find /opt/pimes/data/raw -name '*.lem' | wc -l"))
print(run("find /opt/pimes/data/raw -name '*.lem' -exec du -sh {} + | tail -1"))

print("=" * 60)
print("LFCP PHASE 2: BINARY CHARACTERIZATION")
print("=" * 60)

# Phase 2: Hex dump of different files
# Pick 3 files: smallest, medium, DNP
print("\n--- HEX DUMP: ALR (1.5MB .lem) ---")
alr_hex = run("hexdump -C /opt/pimes/data/raw/ALR/*.lem 2>/dev/null | head -40")
print(alr_hex[:2000])

print("\n--- HEX DUMP: PLU (2.4MB .lem) ---")
plu_hex = run("hexdump -C /opt/pimes/data/raw/PLU/*.lem 2>/dev/null | head -40")
print(plu_hex[:2000])

print("\n--- HEX DUMP: DNP (458MB, first file) ---")
# DNP has 76 files, find the .lem ones
print(run("find /opt/pimes/data/raw/DNP -name '*.lem' -exec ls -la {} \\; 2>/dev/null | head -10"))

# Get hex of first DNP .lem
dnp_first = run("find /opt/pimes/data/raw/DNP -name '*.lem' | head -1")
if dnp_first:
    dnp_hex = run(f"hexdump -C {dnp_first} 2>/dev/null | head -40")
    print(dnp_hex[:2000])
    print(f"\nFile: {dnp_first}")

print("\n--- HEX DUMP: SCN ---")
scn_hex = run("hexdump -C /opt/pimes/data/raw/SCN/*.lem 2>/dev/null | head -40")
print(scn_hex[:2000])

# Also check a non-.lem file for comparison
print("\n--- HEX DUMP: MLB .mlb file (for comparison) ---")
mlb_hex = run("hexdump -C /opt/pimes/data/raw/mlb/S260611.mlb 2>/dev/null | head -40")
print(mlb_hex[:2000])

# Check KINDEX files (cross-station reference)
print("\n--- KINDEX FILES (33 files, cross-station) ---")
print(run("ls -la /opt/pimes/data/raw/KINDEX/ 2>/dev/null | head -40"))

print("\n--- FILE SIZES UNIQUE VALUES ---")
print(run("find /opt/pimes/data/raw -name '*.lem' -exec ls -l {} \\; 2>/dev/null | awk '{print $5}' | sort -n | uniq -c | sort -rn | head -20"))

c.close()
