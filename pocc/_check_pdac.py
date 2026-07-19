import paramiko
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=15)

# Check PDAC outputs
checks = [
    ("REMOTE MANIFEST", "cat /opt/pimes/laws/runtime/validation/pdac/remote_manifest.json 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);print(json.dumps({k:d[k] for k in [\"total_stations\",\"total_files\",\"total_size_gb\",\"latency\"] if k in d},indent=2))'"),
    ("COLLECTOR MANIFEST", "cat /opt/pimes/laws/runtime/validation/pdac/collector_manifest.json 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);print(json.dumps({k:d[k] for k in [\"scheduler_uuid\",\"queue\",\"health\"] if k in d},indent=2))'"),
    ("FILES IN PDAC", "find /opt/pimes/laws/runtime/validation/pdac -type f -name '*.json' 2>/dev/null"),
]

for label, cmd in checks:
    _, o, _ = c.exec_command(cmd)
    out = o.read().decode()[:1500]
    print("\n=== %s ===" % label)
    print(out if out.strip() else "(empty)")

c.close()
