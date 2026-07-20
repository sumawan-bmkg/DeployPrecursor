#!/usr/bin/env python3
"""LAWS V2 Full Deploy — collector + scientific_qg + backend + deps.

Usage:
    python _deploy_laws_v2.py            # deploy everything
    python _deploy_laws_v2.py quick      # skip tests + reinstall
    python _deploy_laws_v2.py verify     # check only
    python _deploy_laws_v2.py collector  # collector + scientific_qg only
"""
import paramiko, base64, os, sys, time, json, hashlib, traceback
from pathlib import Path

HOST = "10.20.229.43"
USER = "bmkg"
PASS = "precursor@admin2026!"
LOCAL = Path(r"d:\opt\pimes\pocc")
REMOTE = "/opt/pimes/pocc"
VENV = "/opt/pimes/laws/runtime/.venv/bin/python"
PORT = 8500

# ── Persistent connections ──
_c = None
_sftp = None

def ssh():
    global _c
    try:
        if _c:
            _c.exec_command("echo ok", timeout=5)
            return _c
    except:
        _c = None
    _c = paramiko.SSHClient()
    _c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    _c.connect(HOST, username=USER, password=PASS, timeout=20)
    return _c

def sftp():
    global _sftp, _c
    try:
        if _sftp:
            _sftp.listdir(".")
            return _sftp
    except:
        _sftp = None
    _sftp = ssh().open_sftp()
    return _sftp

def run(cmd, timeout=30):
    _, o, e = ssh().exec_command(cmd, timeout=timeout)
    return o.read().decode().strip()

def sha256(p):
    try:
        return hashlib.sha256(open(str(p), "rb").read()).hexdigest()[:16]
    except:
        return ""

def remote_hash(path):
    h = run(f"sha256sum {path} 2>/dev/null | cut -d' ' -f1")[:16]
    return h if h else ""

def upload_file(local, remote, retries=3):
    """Upload via SFTP, verify hash. Reuses persistent connection."""
    remote = remote.replace("\\", "/")
    ssh().exec_command(f"mkdir -p {os.path.dirname(remote)}")
    lh = sha256(local)

    for attempt in range(retries):
        try:
            sf = sftp()
            sf.put(str(local), remote)
            rh = remote_hash(remote)
            if lh == rh:
                return True
            print(f"      Hash mismatch (attempt {attempt+1}), retrying...")
        except Exception as e:
            if attempt < retries - 1:
                print(f"      Retry {attempt+1}/{retries}: {e}")
                global _sftp, _c
                _sftp = None; _c = None  # force reconnect
                time.sleep(2)
            else:
                print(f"      FAIL after {retries} retries: {os.path.basename(local)}")
                return False
    return False

def collect_files(base_dir, prefix, exclude=None):
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

    changed = 0
    uploaded = 0
    skipped = 0

    # ── File manifest ──
    files = []

    if mode in ("full", "collector", "quick"):
        files.extend(collect_files(LOCAL / "collector", "collector/"))
        files.extend(collect_files(LOCAL / "collector/scientific_qg", "collector/scientific_qg/"))

    if mode in ("full", "quick"):
        for ld, rd in [
            (LOCAL / "backend", f"{REMOTE}/backend"),
            (LOCAL / "backend/templates", f"{REMOTE}/backend/templates"),
        ]:
            files.extend(collect_files(ld, str(ld.name) + "/"))
        for ld in [LOCAL / "backend/static/css", LOCAL / "backend/static/js", LOCAL / "backend/static/img"]:
            if ld.exists():
                files.extend(collect_files(ld, str(ld.relative_to(LOCAL)).replace("\\", "/")))

    # ── Analyze ──
    print("  [1] Analyzing...")
    # Batch hash check via single remote command
    check_script = "echo '---'; "
    for local, remote in files:
        check_script += f"echo 'CHECK:{remote}'; sha256sum {remote} 2>/dev/null || echo 'MISSING:{remote}'; "
    check_script += "echo '---'"
    out = run(check_script, timeout=60)
    remote_hashes = {}
    for line in out.strip().split("\n"):
        line = line.strip()
        if line.startswith("CHECK:"):
            parts = line.split()
            if len(parts) >= 2:
                fp = parts[0].replace("CHECK:", "")
                h = parts[1] if len(parts) > 1 else ""
                remote_hashes[fp] = h[:16]
        elif line.startswith("MISSING:"):
            fp = line.replace("MISSING:", "")
            remote_hashes[fp] = ""

    for local, remote in files:
        lh = sha256(local)
        rh = remote_hashes.get(remote, "")
        if lh == rh:
            skipped += 1
        else:
            changed += 1
    print(f"      Changed: {changed}, Skipped: {skipped}")

    if mode == "verify":
        print(f"      Remote ready: {skipped}/{skipped+changed} files match\n")
        return

    if changed == 0:
        print("      No changes.\n")

    # ── Upload ──
    if changed > 0:
        print("  [2] Uploading...")
        # Ensure remote dirs exist (batch)
        dirs = sorted(set(os.path.dirname(r) for _, r in files))
        for d in dirs:
            ssh().exec_command(f"mkdir -p {d}")

        for local, remote in files:
            lh = sha256(local)
            rh = remote_hashes.get(remote, "")
            if lh == rh:
                continue
            ok = upload_file(local, remote)
            if ok:
                uploaded += 1
                if uploaded % 20 == 0:
                    print(f"      Progress: {uploaded}/{changed}")
        print(f"      Uploaded: {uploaded}/{changed}")

    # ── Dependencies ──
    if mode != "collector":
        print("  [3] Dependencies...")
        deps_ok = True
        for pkg in ["numpy", "scipy", "paramiko", "fastapi", "uvicorn", "pydantic", "yaml"]:
            ok = run(f"{VENV} -c 'import {pkg}' 2>&1") == ""
            if not ok:
                run(f"{VENV} -m pip install {pkg} -q 2>&1 | tail -1")
            deps_ok = deps_ok and (run(f"{VENV} -c 'import {pkg}' 2>&1") == "")
        print(f"      {'All OK' if deps_ok else 'Some failed'}")

    # ── Restart ──
    print("  [4] Restarting...")
    ssh().exec_command("pkill -f 'collector.scheduler' 2>/dev/null")
    ssh().exec_command("pkill -f 'collector.__main__' 2>/dev/null")
    time.sleep(1)
    ssh().exec_command(f"pkill -f 'uvicorn.*backend.main' 2>/dev/null")
    time.sleep(1)

    ssh().exec_command(f"cd {REMOTE} && nohup {VENV} -m uvicorn backend.main:app --host 0.0.0.0 --port {PORT} > {REMOTE}/pocc.log 2>&1 </dev/null &")
    time.sleep(4)
    h = run(f"curl -s -o /dev/null -w '%{{http_code}}' http://127.0.0.1:{PORT}/api/health 2>/dev/null")
    backend_ok = h == "200"
    print(f"      Backend: {'OK' if backend_ok else f'FAIL ({h})'}")

    if mode in ("full", "collector", "quick"):
        # Start collector — don't wait for stdout
        ssh().exec_command(f"cd {REMOTE} && nohup {VENV} -m collector > {REMOTE}/collector.log 2>&1 </dev/null &")
        time.sleep(3)
        col = run("ps aux | grep -c '[c]ollector' || echo 0")
        collector_ok = int(col) > 0
        print(f"      Collector: {'OK' if collector_ok else 'STOPPED'}")

    elapsed = time.time() - start
    print(f"\n  Done ({elapsed:.0f}s)")
    print(f"{'='*40}\n")

    # Cleanup
    global _sftp, _c
    try:
        if _sftp: _sftp.close()
    except: pass
    try:
        if _c: _c.close()
    except: pass


if __name__ == "__main__":
    deploy()
