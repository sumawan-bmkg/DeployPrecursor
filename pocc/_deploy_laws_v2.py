#!/usr/bin/env python3
"""LAWS V2 Full Deploy — collector + scientific_qg + backend + deps.

Usage:
    python _deploy_laws_v2.py            # deploy everything
    python _deploy_laws_v2.py quick      # skip tests + reinstall
    python _deploy_laws_v2.py verify     # check only
    python _deploy_laws_v2.py collector  # collector + scientific_qg only
"""
import paramiko, base64, os, sys, time, json, hashlib
from pathlib import Path

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"
LOCAL = Path(r"d:\opt\pimes\pocc")
REMOTE = "/opt/pimes/pocc"
VENV = "/opt/pimes/laws/runtime/.venv/bin/python"
PORT = 8500

_c = None
def ssh():
    global _c
    try:
        if _c:
            _c.exec_command("echo ok", timeout=3)
            return _c
    except:
        _c = None
    _c = paramiko.SSHClient()
    _c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    _c.connect(HOST, username=USER, password=PASS, timeout=15)
    return _c

def run(cmd, timeout=30):
    _, o, e = ssh().exec_command(cmd, timeout=timeout)
    return o.read().decode().strip()

def sha256(p):
    try:
        return hashlib.sha256(open(str(p), "rb").read()).hexdigest()[:16]
    except:
        return ""

def upload_file(local, remote):
    """Upload via base64 script, verify size+hash."""
    remote = remote.replace("\\", "/")
    ssh().exec_command(f"mkdir -p {os.path.dirname(remote)}")
    data = base64.b64encode(open(str(local), "rb").read()).decode()
    script = f'import base64; open("{remote}","wb").write(base64.b64decode("""{data}"""))'
    Path("_pdm_tmp.py").write_text(script)
    sftp = ssh().open_sftp()
    sftp.put("_pdm_tmp.py", "/tmp/_pdm_tmp.py")
    sftp.close()
    run(f"python3 /tmp/_pdm_tmp.py && rm /tmp/_pdm_tmp.py")
    Path("_pdm_tmp.py").unlink(missing_ok=True)
    # Verify
    local_sz = os.path.getsize(str(local))
    rhash = run(f"sha256sum {remote} 2>/dev/null | cut -d' ' -f1")[:16]
    return sha256(str(local)) == rhash

def collect_files(base_dir, prefix, exclude=None):
    """Get (local_path, remote_path) for all .py in base_dir."""
    exclude = exclude or {"__pycache__"}
    files = []
    for f in sorted(Path(base_dir).rglob("*")):
        if not f.is_file():
            continue
        if any(ex in str(f) for ex in exclude):
            continue
        rel = str(f.relative_to(LOCAL)).replace("\\", "/")
        files.append((str(f), f"{REMOTE}/{rel}"))
    return files

def deploy():
    mode = sys.argv[1] if len(sys.argv) > 1 else "full"
    start = time.time()
    print(f"\n{'='*40}")
    print(f" LAWS V2 Deploy — {mode}")
    print(f"{'='*40}\n")

    c = ssh()
    changed = 0
    uploaded = 0
    skipped = 0

    # ── File manifest ──
    files = []

    if mode in ("full", "collector", "quick"):
        # collector/*.py
        files.extend(collect_files(LOCAL / "collector", "collector/"))
        # scientific_qg/
        files.extend(collect_files(LOCAL / "collector/scientific_qg", "collector/scientific_qg/"))

    if mode in ("full", "quick"):
        # backend
        for ld, rd in [
            (LOCAL / "backend", f"{REMOTE}/backend"),
            (LOCAL / "backend/templates", f"{REMOTE}/backend/templates"),
        ]:
            files.extend(collect_files(ld, str(ld.name) + "/"))
        # static
        for ld in [LOCAL / "backend/static/css", LOCAL / "backend/static/js", LOCAL / "backend/static/img"]:
            if ld.exists():
                files.extend(collect_files(ld, str(ld.relative_to(LOCAL)).replace("\\", "/")))

    # ── Analyze ──
    print("  [1] Analyzing...")
    for local, remote in files:
        lh = sha256(local)
        rh = run(f"sha256sum {remote} 2>/dev/null | cut -d' ' -f1")[:16]
        if lh == rh:
            skipped += 1
        else:
            changed += 1
    print(f"      Changed: {changed}, Skipped: {skipped}")

    if changed == 0 and mode != "verify":
        print("      No changes.\n")

    if mode == "verify":
        print(f"      Remote ready: {skipped}/{skipped+changed} files match\n")
        return

    # ── Upload ──
    if changed > 0:
        print("  [2] Uploading...")
        for local, remote in files:
            lh = sha256(local)
            rh = run(f"sha256sum {remote} 2>/dev/null | cut -d' ' -f1")[:16]
            if lh == rh:
                continue
            ok = upload_file(local, remote)
            if ok:
                uploaded += 1
            else:
                print(f"      FAIL: {os.path.basename(local)}")
        print(f"      Uploaded: {uploaded}/{changed}")

    # ── Dependencies ──
    if mode != "collector":
        print("  [3] Dependencies...")
        deps_ok = True
        for pkg in ["numpy", "scipy", "paramiko", "fastapi", "uvicorn", "pydantic", "yaml"]:
            ok = run(f"{VENV} -c 'import {pkg}' 2>&1") == ""
            if not ok:
                print(f"      Installing {pkg}...")
                run(f"{VENV} -m pip install {pkg} -q 2>&1 | tail -1")
            deps_ok = deps_ok and (run(f"{VENV} -c 'import {pkg}' 2>&1") == "")
        print(f"      {'All OK' if deps_ok else 'Some failed'}")

    # ── Restart ──
    print("  [4] Restarting...")
    # Kill collector
    run("pkill -f 'collector.scheduler' 2>/dev/null")
    run("pkill -f 'collector.__main__' 2>/dev/null")
    time.sleep(1)
    # Kill backend
    run("pkill -f 'uvicorn.*backend.main' 2>/dev/null")
    time.sleep(1)

    # Start backend
    run(f"cd {REMOTE} && nohup {VENV} -m uvicorn backend.main:app --host 0.0.0.0 --port {PORT} > {REMOTE}/pocc.log 2>&1 </dev/null &")
    time.sleep(3)

    # Verify
    h = run(f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:{PORT}/api/health 2>/dev/null")
    backend_ok = h == "200"
    print(f"      Backend: {'OK' if backend_ok else f'FAIL ({h})'}")

    # Start collector
    if mode in ("full", "collector", "quick"):
        run(f"cd {REMOTE} && nohup {VENV} -m collector > {REMOTE}/collector.log 2>&1 </dev/null &")
        time.sleep(2)
        col = run("ps aux | grep -c '[c]ollector' || echo 0")
        collector_ok = int(col) > 0
        print(f"      Collector: {'OK' if collector_ok else 'STOPPED'}")

    elapsed = time.time() - start
    print(f"\n  Done ({elapsed:.0f}s)")
    print(f"{'='*40}\n")


if __name__ == "__main__":
    deploy()
