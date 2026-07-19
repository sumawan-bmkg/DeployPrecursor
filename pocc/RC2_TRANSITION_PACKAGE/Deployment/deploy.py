"""
PIMES Deployment Manager (PDM) — Single Entry Point.

Usage:
  python deploy.py [command]

Commands:
  (none)         Deploy
  status         Operational status
  doctor         Health check
  rollback       Rollback to last backup
  emergency      Emergency: rollback + health
  campaign       Campaign status
  shadow         Shadow readiness check
  rc             RC readiness check
  audit          Full audit (SOQ/CSQ/CEPSL/OSC)
  release        Build release package
  report         Generate reports
  replay         Replay last deploy
  dashboard      Open dashboard URL
  watch          Live monitoring
  wizard         Interactive mode
  maintenance    Toggle maintenance mode
"""
import paramiko, base64, time, json, hashlib, os, sys
from pathlib import Path
from datetime import datetime, timezone

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"
LOCAL = Path(r"d:\opt\pimes\pocc")
REMOTE = "/opt/pimes/pocc"
PORT = 8500
URL = f"http://{HOST}:{PORT}"

# ── Helpers ──────────────────────────────────────────────
def now(): return datetime.now(timezone.utc).isoformat()
def ts(): return datetime.now().strftime("%Y%m%d_%H%M%S")
def uid(): return str(__import__("uuid").uuid4())[:8]
def sha256(p):
    try: return hashlib.sha256(open(p,"rb").read()).hexdigest()[:16]
    except: return "N/A"
def ensure(d):
    Path(d).mkdir(parents=True, exist_ok=True)

_c = None
def ssh():
    global _c
    try:
        if _c: _c.exec_command("echo ok", timeout=3); return _c
    except: _c = None
    _c = paramiko.SSHClient()
    _c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    _c.connect(HOST, username=USER, password=PASS, timeout=10)
    return _c

def run(cmd):
    _, o, _ = ssh().exec_command(cmd)
    return o.read().decode().strip()

def health_ok():
    return run("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/api/health 2>/dev/null") == "200"

# ── STATUS ───────────────────────────────────────────────
def cmd_status():
    c = ssh()
    h = run("curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8500/api/health 2>/dev/null")
    uvi = run("ps aux | grep -c '[u]vicorn.*8500' || echo 0")
    col = run("ps aux | grep -c '[c]ollector' || echo 0")
    disk = run("df -h /opt/pimes | tail -1 | awk '{print $5}'")
    try:
        cep = json.loads(run("cat /opt/pimes/posc/osc/data/cepsl_status.json 2>/dev/null || echo '{}'"))
    except: cep = {}
    try:
        shad = json.loads(run("cat /opt/pimes/posc/osc/data/shadow_readiness.json 2>/dev/null || echo '{}'"))
    except: shad = {}

    day = cep.get("campaign_day", "?")
    baseline = "VALID" if cep.get("baseline_valid") else "COMPROMISED"
    snap = cep.get("archive_verified", 0)
    shadow = shad.get("decision", "?")

    pages = ["/", "/collector", "/runtime", "/executive", "/governance", "/reports", "/deployment", "/system", "/shadow", "/stations"]
    up = sum(1 for p in pages if run(f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:8500{p} 2>/dev/null") == "200")

    score = 100 if h == "200" else 0
    if int(col or 0) == 0: score -= 20
    if up < len(pages): score -= (len(pages) - up) * 2

    print(f"\n{'='*40}")
    print(f" PIMES Operational Status")
    print(f"{'='*40}")
    print(f"  System        : {'HEALTHY' if h=='200' else 'DEGRADED'}")
    print(f"  Collector     : {'RUNNING' if int(col or 0) > 0 else 'STOPPED'}")
    print(f"  Dashboard     : {up}/{len(pages)} pages")
    print(f"  Disk          : {disk}")
    print(f"  Campaign Day  : {day}")
    print(f"  CEPSL         : {baseline}")
    print(f"  Snapshots     : {snap}")
    print(f"  Shadow Gate   : {shadow}")
    print(f"  Overall       : {score}%")
    print(f"{'='*40}\n")

# ── DOCTOR ───────────────────────────────────────────────
def cmd_doctor():
    print(f"\n{'='*40}")
    print(f" PIMES Doctor")
    print(f"{'='*40}")
    c = ssh()
    checks = [
        ("SSH",     lambda: True),
        ("Disk",    lambda: float(run("df -h /opt/pimes | tail -1 | awk '{print $5}'").rstrip('%')) < 90),
        ("RAM",     lambda: float(run("free -h | grep Mem | awk '{print $3/$2*100}'") or 100) < 90),
        ("Python",  lambda: "3." in run(f"/opt/pimes/laws/runtime/.venv/bin/python3 --version")),
        ("BOCC",    lambda: health_ok()),
        ("Collector", lambda: int(run("ps aux | grep -c '[c]ollector' || echo 0")) > 0),
        ("OSC Cron", lambda: int(run("crontab -l 2>/dev/null | grep -c osc || echo 0")) >= 2),
    ]
    passed = 0
    for name, check in checks:
        ok = False
        try: ok = check()
        except: pass
        if ok: passed += 1
        print(f"  {'✓' if ok else '✗'} {name}")

    # APIs
    for path, name in [("/api/health","API"), ("/api/cepsl","CEPSL"), ("/api/csq/scores","CSQ")]:
        code = run(f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:8500{path} 2>/dev/null")
        ok = code == "200"
        if ok: passed += 1
        print(f"  {'✓' if ok else '✗'} {name}")

    total = passed + 2  # pages + campaign
    pages = sum(1 for p in ["/", "/collector", "/runtime", "/executive", "/governance", "/reports", "/deployment", "/system", "/shadow", "/stations"]
                if run(f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:8500{p} 2>/dev/null") == "200")
    if pages == 10: passed += 1
    print(f"  {'✓' if pages==10 else '✗'} Dashboard ({pages}/10)")

    try:
        cep = json.loads(run("cat /opt/pimes/posc/osc/data/cepsl_status.json 2>/dev/null || echo '{}'"))
        day_ok = int(cep.get("campaign_day", 0)) > 0
        if day_ok: passed += 1
        print(f"  {'✓' if day_ok else '✗'} Campaign (day {cep.get('campaign_day','?')})")
    except:
        print(f"  ✗ Campaign")

    total += 1
    print(f"\n  Result: {passed}/{total} PASS")
    print(f"{'='*40}\n")

# ── DEPLOY ───────────────────────────────────────────────
def cmd_deploy():
    ensure(LOCAL / "release")
    start = time.time()
    dep_id = uid()
    print(f"\n{'='*40}")
    print(f" PIMES Deploy")
    print(f"{'='*40}\n")

    # Risk
    c = ssh()
    changed = 0
    skipped = 0
    sftp = c.open_sftp()
    print("  [1] Analyzing...")

    # Count changes
    for ld, rd in [(LOCAL/"backend", f"{REMOTE}/backend"), (LOCAL/"backend/templates", f"{REMOTE}/backend/templates")]:
        for f in sorted(ld.rglob("*")):
            if not f.is_file(): continue
            if "__pycache__" in str(f): continue
            rel = str(f.relative_to(ld)).replace("\\","/")
            remote = f"{rd}/{rel}"
            lh = sha256(str(f))
            rh = run(f"sha256sum {remote} 2>/dev/null | cut -d' ' -f1")
            if lh != rh: changed += 1
            else: skipped += 1
    print(f"      Changed: {changed}, Unchanged: {skipped}")

    if changed == 0:
        print("      No changes. Done.\n")
        return

    risk = "LOW" if changed < 5 else "MEDIUM" if changed < 20 else "HIGH"
    print(f"      Risk: {risk}")

    # Backup
    print("  [2] Backing up...")
    bk = f"/opt/pimes/backup/{ts()}"
    run(f"mkdir -p {bk} && cp -r /opt/pimes/pocc/backend {bk}/ && cp -r /opt/pimes/pocc/validation {bk}/")
    print(f"      OK: {bk}")

    # Upload
    print("  [3] Uploading...")
    uploaded = 0
    for ld, rd in [(LOCAL/"backend", f"{REMOTE}/backend"), (LOCAL/"backend/templates", f"{REMOTE}/backend/templates")]:
        for f in sorted(ld.rglob("*")):
            if not f.is_file(): continue
            if "__pycache__" in str(f): continue
            rel = str(f.relative_to(ld)).replace("\\","/")
            remote = f"{rd}/{rel}"
            lh = sha256(str(f))
            rh = run(f"sha256sum {remote} 2>/dev/null | cut -d' ' -f1")
            if lh == rh: continue
            b64 = base64.b64encode(open(f,"rb").read()).decode()
            Path("_pdm_tmp.py").write_text(f'import base64; open("{remote}","wb").write(base64.b64decode("{b64}"))')
            try:
                sftp.put("_pdm_tmp.py", "/tmp/_pdm_tmp.py")
                run(f"python3 /tmp/_pdm_tmp.py && rm /tmp/_pdm_tmp.py")
                uploaded += 1
            except: pass
    sftp.close()
    Path("_pdm_tmp.py").unlink(missing_ok=True)
    print(f"      Uploaded: {uploaded} files")

    # Restart
    print("  [4] Restarting...")
    run(f"pkill -f 'uvicorn.*backend.main' 2>/dev/null; sleep 2")
    run(f"cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port {PORT} > pocc.log 2>&1 </dev/null &")
    time.sleep(5)
    ok = health_ok()
    print(f"      {'OK' if ok else 'FAIL'}")

    if not ok:
        print("  [!] Auto-rollback triggered...")
        run(f"rm -rf {REMOTE}/backend/* && cp -r {bk}/backend/* {REMOTE}/backend/")
        run(f"rm -rf {REMOTE}/validation/* && cp -r {bk}/validation/* {REMOTE}/validation/")
        run(f"pkill -f 'uvicorn.*backend.main' 2>/dev/null; sleep 2")
        run(f"cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port {PORT} > pocc.log 2>&1 </dev/null &")
        time.sleep(5)
        ok = health_ok()
        print(f"      Rollback: {'OK' if ok else 'FAIL'}")
        return

    # Verify
    print("  [5] Verifying...")
    pages_ok = sum(1 for p in ["/","/collector","/runtime","/executive","/governance","/reports","/deployment","/system","/shadow","/stations"]
                   if run(f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:8500{p} 2>/dev/null") == "200")
    apis_ok = sum(1 for a in ["/api/health","/api/infrastructure","/api/cepsl","/api/csq/scores","/api/shadow/readiness"]
                  if run(f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:8500{a} 2>/dev/null") == "200")
    print(f"      Pages: {pages_ok}/10, APIs: {apis_ok}/5")

    elapsed = time.time() - start

    # Certificate
    cert = f"""Deploy {dep_id} | {now()[:19]} | {elapsed:.0f}s | {changed} files | Risk: {risk}
Pages: {pages_ok}/10 | APIs: {apis_ok}/5 | Backup: {bk}
"""
    (LOCAL / "release" / f"deploy_{dep_id}.txt").write_text(cert)

    # Save manifest
    (LOCAL / "manifests").mkdir(exist_ok=True)
    (LOCAL / "manifests" / f"deploy_{ts()}.json").write_text(json.dumps({
        "id": dep_id, "ts": now(), "elapsed_s": round(elapsed,1),
        "changed": changed, "uploaded": uploaded, "risk": risk,
        "pages": pages_ok, "apis": apis_ok, "backup": bk,
    }, indent=2))

    print(f"  [6] DONE ({elapsed:.0f}s)")
    print(f"      Certificate: deploy_{dep_id}.txt\n")

# ── ROLLBACK ─────────────────────────────────────────────
def cmd_rollback():
    c = ssh()
    print(f"\n{'='*40}")
    print(f" PIMES Rollback")
    print(f"{'='*40}\n")
    backups = run("ls -1t /opt/pimes/backup 2>/dev/null | head -3")
    if not backups.strip():
        print("  No backups found.\n"); return
    latest = backups.strip().split("\n")[0]
    print(f"  Restoring: {latest}")
    run(f"rm -rf /opt/pimes/pocc/backend/* && cp -r /opt/pimes/backup/{latest}/backend/* /opt/pimes/pocc/backend/")
    print("  Restarting...")
    run("pkill -f 'uvicorn.*backend.main' 2>/dev/null; sleep 2")
    run(f"cd /opt/pimes/pocc && nohup /opt/pimes/laws/runtime/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port {PORT} > pocc.log 2>&1 </dev/null &")
    time.sleep(5)
    ok = health_ok()
    print(f"  Health: {'OK' if ok else 'FAIL'}\n")

# ── EMERGENCY ────────────────────────────────────────────
def cmd_emergency():
    print(f"\n{'='*40}")
    print(f" PIMES Emergency")
    print(f"{'='*40}\n")
    cmd_rollback()
    cmd_doctor()
    cmd_status()

# ── CAMPAIGN ─────────────────────────────────────────────
def cmd_campaign():
    c = ssh()
    try: cep = json.loads(run("cat /opt/pimes/posc/osc/data/cepsl_status.json 2>/dev/null || echo '{}'"))
    except: cep = {}
    try: shad = json.loads(run("cat /opt/pimes/posc/osc/data/shadow_readiness.json 2>/dev/null || echo '{}'"))
    except: shad = {}

    day = int(cep.get("campaign_day", 0))
    print(f"\n{'='*40}")
    print(f" PIMES Campaign")
    print(f"{'='*40}")
    print(f"  Day            : {day}")
    print(f"  Remaining      : {max(0, 14-day)}")
    print(f"  Baseline       : {'VALID' if cep.get('baseline_valid') else 'COMPROMISED'}")
    print(f"  Snapshots      : {cep.get('archive_verified', 0)}")
    print(f"  Shadow Ready   : {'YES' if cep.get('shadow_eligible') else 'NO'}")
    print(f"  Decision       : {shad.get('decision', 'N/A')}")
    print(f"{'='*40}\n")

# ── SHADOW ───────────────────────────────────────────────
def cmd_shadow():
    c = ssh()
    try: cep = json.loads(run("cat /opt/pimes/posc/osc/data/cepsl_status.json 2>/dev/null || echo '{}'"))
    except: cep = {}
    try: shad = json.loads(run("cat /opt/pimes/posc/osc/data/shadow_readiness.json 2>/dev/null || echo '{}'"))
    except: shad = {}
    try: csq = json.loads(run("cat /opt/pimes/posc/csq/data/qualification_current.json 2>/dev/null || echo '{}'"))
    except: csq = {}

    day = int(cep.get("campaign_day", 0))
    overall = shad.get("overall", 0)
    score = float(overall) if overall else 0
    eligible = score >= 70 and day >= 14
    print(f"\n{'='*40}")
    print(f" Shadow Readiness")
    print(f"{'='*40}")
    print(f"  Data Days      : {day}/14")
    print(f"  Health         : {cep.get('scores',{}).get('collector',0)}%")
    print(f"  OSC Baseline   : {'VALID' if cep.get('baseline_valid') else 'COMPROMISED'}")
    print(f"  CEPSL          : {'VALID' if not cep.get('archive_issues',0) else str(cep.get('archive_issues',0))+' issues'}")
    print(f"  CSQ Score      : {csq.get('score', 'N/A')}%")
    print(f"  Readiness      : {score:.1f}%")
    print(f"  Decision       : {shad.get('decision', 'N/A')}")
    print(f"  Recommendation : {'READY FOR SHADOW' if eligible else f'Not yet — need {max(0,14-day)} more days'}")
    print(f"{'='*40}\n")

# ── RC ───────────────────────────────────────────────────
def cmd_rc():
    c = ssh()
    try: cep = json.loads(run("cat /opt/pimes/posc/osc/data/cepsl_status.json 2>/dev/null || echo '{}'"))
    except: cep = {}
    try: shad = json.loads(run("cat /opt/pimes/posc/osc/data/shadow_readiness.json 2>/dev/null || echo '{}'"))
    except: shad = {}
    burn = run("cat /opt/pimes/laws/runtime/validation/burnin/burnin_status.json 2>/dev/null | python3 -c 'import sys,json;print(json.load(sys.stdin).get(\"status\",\"?\"))' 2>/dev/null || echo N/A")
    psep = run("curl -s http://127.0.0.1:8500/api/health-model 2>/dev/null | python3 -c 'import sys,json;d=json.load(sys.stdin);print(d.get(\"components\",{}).get(\"psep\",{}).get(\"status\",\"?\"))' 2>/dev/null || echo N/A")

    print(f"\n{'='*40}")
    print(f" RC Readiness")
    print(f"{'='*40}")
    print(f"  Burn-in        : {burn}")
    print(f"  PSEP           : {psep}")
    print(f"  OSC Campaign   : Day {cep.get('campaign_day','?')}")
    print(f"  CEPSL          : {'VALID' if cep.get('baseline_valid') else 'COMPROMISED'}")
    print(f"  Shadow         : {shad.get('decision','N/A')}")
    print(f"  Readiness      : {shad.get('overall',0)}%")
    print(f"  Recommendation : RC1 if score>=60, RC2 if score>=70")
    print(f"{'='*40}\n")

# ── AUDIT ────────────────────────────────────────────────
def cmd_audit():
    c = ssh()
    print(f"\n{'='*40}")
    print(f" PIMES Audit")
    print(f"{'='*40}")

    apis = [
        ("/api/health","BOCC"), ("/api/pipeline/stages","Pipeline"), ("/api/infrastructure","Infrastructure"),
        ("/api/cepsl","CEPSL"), ("/api/csq/scores","CSQ"), ("/api/shadow/readiness","Shadow"),
        ("/api/evidence","Evidence"), ("/api/reports","Reports"), ("/api/osc/status","OSC"),
    ]
    passed = 0
    for path, name in apis:
        code = run(f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:8500{path} 2>/dev/null")
        ok = code == "200"
        if ok: passed += 1
        print(f"  {'✓' if ok else '✗'} {name}")

    pages = ["/","/collector","/runtime","/executive","/governance","/reports","/deployment","/system","/shadow","/stations"]
    pages_ok = sum(1 for p in pages if run(f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:8500{p} 2>/dev/null") == "200")
    if pages_ok == 10: passed += 1
    print(f"  {'✓' if pages_ok==10 else '✗'} Dashboard ({pages_ok}/10)")

    try:
        cep = json.loads(run("cat /opt/pimes/posc/osc/data/cepsl_status.json 2>/dev/null || echo '{}'"))
        if cep.get("baseline_valid"): passed += 1
        print(f"  {'✓' if cep.get('baseline_valid') else '✗'} CEPSL Integrity")
    except:
        print(f"  ✗ CEPSL Integrity")

    print(f"\n  Audit Result: {passed}/{len(apis)+2}")
    print(f"{'='*40}\n")

# ── RELEASE ──────────────────────────────────────────────
def cmd_release():
    ensure(LOCAL / "release")
    id = uid()
    ver = ts()
    rd = LOCAL / "release" / f"RC2_{ver}"
    rd.mkdir(exist_ok=True)
    files = []
    for f in sorted(LOCAL.rglob("*")):
        if not f.is_file(): continue
        if any(ex in str(f) for ex in ["__pycache__","release","backup","manifests","reports","node_modules"]): continue
        files.append({"path": str(f.relative_to(LOCAL)).replace("\\","/"), "size": f.stat().st_size, "hash": sha256(str(f))})
    (rd / "manifest.json").write_text(json.dumps({"id": id, "ts": now(), "files": files}, indent=2))
    with open(rd / "sha256.txt", "w") as fh:
        for f in files: fh.write(f"{f['hash']}  {f['path']}\n")
    (rd / "certificate.md").write_text(f"# Release RC2_{ver}\n\nUUID: {id}\nFiles: {len(files)}\nTimestamp: {now()}\n")
    print(f"\n  Release: RC2_{ver}")
    print(f"  Files: {len(files)}")
    print(f"  Path: release/RC2_{ver}/\n")

# ── REPORT ───────────────────────────────────────────────
def cmd_report():
    c = ssh()
    files = sorted(Path(LOCAL / "manifests").glob("deploy_*.json"), reverse=True)
    print(f"\n{'='*40}")
    print(f" PIMES Reports")
    print(f"{'='*40}")
    for f in files[:3]:
        d = json.loads(f.read_text())
        print(f"  {d['ts'][:19]} | {d['elapsed_s']}s | {d.get('changed',0)} files | {d.get('risk','?')}")
    if not files:
        print("  No deployments yet.")
    print(f"{'='*40}\n")

# ── REPLAY ───────────────────────────────────────────────
def cmd_replay():
    files = sorted(Path(LOCAL / "manifests").glob("deploy_*.json"), reverse=True)
    if not files:
        print("  No deployments to replay."); return
    d = json.loads(files[0].read_text())
    print(f"\n  Replay deploy {d['id']} from {d['ts'][:19]}:")
    print(f"    Changed: {d.get('changed',0)} files")
    print(f"    Risk: {d.get('risk','?')}")
    print(f"    Pages: {d.get('pages','?')}/10")
    print(f"    Duration: {d.get('elapsed_s','?')}s\n")

# ── WATCH ────────────────────────────────────────────────
def cmd_watch():
    print("\n  PIMES Watch (Ctrl+C to stop)\n")
    try:
        while True:
            c = ssh()
            h = health_ok()
            col = run("ps aux | grep -c '[c]ollector' || echo 0")
            try: cep = json.loads(run("cat /opt/pimes/posc/osc/data/cepsl_status.json 2>/dev/null || echo '{}'"))
            except: cep = {}
            try: shad = json.loads(run("cat /opt/pimes/posc/osc/data/shadow_readiness.json 2>/dev/null || echo '{}'"))
            except: shad = {}
            os.system('cls' if os.name == 'nt' else 'clear')
            print(f" PIMES Watch — {datetime.now().strftime('%H:%M:%S')}\n")
            print(f"  System    : {'HEALTHY' if h else 'DEGRADED'}")
            print(f"  Collector : {'RUNNING' if int(col) > 0 else 'STOPPED'}")
            print(f"  Day       : {cep.get('campaign_day','?')}")
            print(f"  CEPSL     : {'VALID' if cep.get('baseline_valid') else 'COMPROMISED'}")
            print(f"  Shadow    : {shad.get('decision','?')}")
            time.sleep(5)
    except KeyboardInterrupt:
        print("\n  Watch stopped.\n")

# ── DASHBOARD ────────────────────────────────────────────
def cmd_dashboard():
    print(f"\n  Opening {URL}\n")
    try:
        import webbrowser
        webbrowser.open(URL)
    except:
        print(f"  Navigate to: {URL}\n")

# ── WIZARD ───────────────────────────────────────────────
def cmd_wizard():
    c = ssh()
    h = health_ok()
    try: cep = json.loads(run("cat /opt/pimes/posc/osc/data/cepsl_status.json 2>/dev/null || echo '{}'"))
    except: cep = {}
    day = cep.get("campaign_day", "?")

    print(f"\n{'='*40}")
    print(f" PIMES Wizard")
    print(f"{'='*40}")
    print(f"  Version        : v2.0.0-rc2")
    print(f"  Health         : {'OK' if h else 'FAIL'}")
    print(f"  Campaign       : Day {day}")
    print(f"  CEPSL          : {'VALID' if cep.get('baseline_valid') else 'COMPROMISED'}")
    print(f"{'='*40}\n")
    print(f"  1. Deploy Update")
    print(f"  2. Health Check")
    print(f"  3. Campaign Status")
    print(f"  4. Shadow Readiness")
    print(f"  5. RC Readiness")
    print(f"  6. Rollback")
    print(f"  7. Audit")
    print(f"  8. Exit\n")

    try:
        choice = input("  Choose (1-8): ").strip()
    except: choice = "8"

    cmds = {"1": cmd_deploy, "2": cmd_doctor, "3": cmd_campaign,
            "4": cmd_shadow, "5": cmd_rc, "6": cmd_rollback,
            "7": cmd_audit, "8": lambda: print("  Bye.\n")}
    (cmds.get(choice, lambda: print("  Invalid."))())

# ── MAINTENANCE ──────────────────────────────────────────
def cmd_maintenance(state):
    if state == "on":
        run("echo '{\"maintenance\":true}' | tee /opt/pimes/posc/osc/data/maintenance.json")
        print("  Maintenance ON")
    else:
        run("rm -f /opt/pimes/posc/osc/data/maintenance.json")
        print("  Maintenance OFF")

# ── MAIN ─────────────────────────────────────────────────
COMMANDS = {
    "status": cmd_status, "doctor": cmd_doctor,
    "rollback": cmd_rollback, "emergency": cmd_emergency,
    "campaign": cmd_campaign, "shadow": cmd_shadow, "rc": cmd_rc,
    "audit": cmd_audit, "release": cmd_release,
    "report": cmd_report, "replay": cmd_replay,
    "watch": cmd_watch, "dashboard": cmd_dashboard,
    "wizard": cmd_wizard,
}

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        cmd_deploy()
    elif args[0] == "maintenance":
        cmd_maintenance(args[1] if len(args) > 1 else "off")
    elif args[0] in COMMANDS:
        COMMANDS[args[0]]()
    else:
        print(f"  Unknown: {args[0]}\n{__doc__}")
