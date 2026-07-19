import paramiko, json

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect("10.20.229.43", username="bmkg", password="precursor@admin2026!", timeout=10)

# 1. Pipeline stages - burn-in, psep, shadow
_, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/pipeline/stages")
raw = o.read().decode()
try:
    stages = json.loads(raw).get("stages", [])
    print("=== PIPELINE VALIDATION STAGES ===")
    for s in stages:
        cat = s.get("category", "")
        if cat in ("validation", "deployment"):
            h = s.get("hash") or "N/A"
            print(f"  {s['label']:12s} | {s['status']:10s} | score={s['score']:.1f} | hash={h}")
    print()
    print("=== ALL STAGES ===")
    for s in stages:
        print(f"  {s['label']:12s} | {s['category']:12s} | {s['status']:10s} | {s['score']:.1f}")
except:
    print("Pipeline API failed")

# 2. Burn-in directory
print("\n=== BURN-IN DIRECTORY ===")
_, o, _ = c.exec_command("ls -la /opt/pimes/laws/runtime/validation/burnin/ 2>/dev/null || echo 'DIR NOT FOUND'")
print(o.read().decode()[:500])

# 3. PSEP directory
print("\n=== PSEP DIRECTORY ===")
_, o, _ = c.exec_command("ls -la /opt/pimes/laws/runtime/validation/psep/ 2>/dev/null || echo 'DIR NOT FOUND'")
print(o.read().decode()[:500])

# 4. PSEP dual execution
print("\n=== PSEP DUAL EXECUTION ===")
_, o, _ = c.exec_command("ls -la /opt/pimes/laws/runtime/validation/psep/dual_execution/ 2>/dev/null || echo 'NOT FOUND'")
print(o.read().decode()[:300])

# 5. Shadow directory
print("\n=== SHADOW DIRECTORY ===")
_, o, _ = c.exec_command("ls -la /opt/pimes/laws/runtime/validation/shadow/ 2>/dev/null || echo 'DIR NOT FOUND'")
print(o.read().decode()[:300])

# 6. Health model
print("\n=== HEALTH MODEL ===")
_, o, _ = c.exec_command("curl -s http://127.0.0.1:8500/api/health-model 2>/dev/null | python3 -c 'import sys,json;h=json.load(sys.stdin);c=h.get(\"components\",{});print(f\"  Score: {h.get(\"score\",0):.1f}%\");[print(f\"  {k}: {v.get(\"score\",0):.1f}%  status={v.get(\"status\",\"?\")}\") for k,v in c.items()]' 2>/dev/null")
print(o.read().decode()[:500])

# 7. Dashboard status (all pages)
print("\n=== DASHBOARD PAGES ===")
pages = ["/", "/engineering", "/scientific-ops", "/pipeline-runtime",
         "/alert-center", "/evidence-center", "/release-center",
         "/executive-center", "/digitaltwin", "/governance", "/governance"]
for p in pages:
    _, o, _ = c.exec_command(f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:8500{p}")
    code = o.read().decode().strip()
    tag = "OK" if code == "200" else f"HTTP_{code}"
    print(f"  {tag:8s} {p}")

c.close()
