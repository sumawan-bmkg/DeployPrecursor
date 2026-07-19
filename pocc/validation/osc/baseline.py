"""OSC Phase 1 — Baseline Freeze. SHA256 all components."""
import json, hashlib, os
from pathlib import Path
from .config import POCC, PDAC, BASELINE
from .utils import now_iso, ensure_dirs

def dir_hash(path):
    if not path.exists(): return "N/A"
    h = hashlib.sha256()
    for f in sorted(path.rglob("*")):
        if f.is_file() and not f.suffix in (".pyc", ".pyo") and "__pycache__" not in str(f):
            h.update(f.name.encode())
            try: h.update(open(f, "rb").read())
            except: pass
    return h.hexdigest()[:32]

def freeze():
    ensure_dirs()
    print("  Freezing baseline...")
    manifest = {
        "ts": now_iso(),
        "dashboard_code": dir_hash(POCC / "backend"),
        "collector_config": str((PDAC / "collector_manifest.json").stat().st_mtime) if (PDAC / "collector_manifest.json").exists() else "N/A",
        "pocc_root": dir_hash(POCC),
        "runtime_dir": dir_hash(POCC.parent / "laws" / "runtime"),
    }

    # System info
    for cmd, key in [("python3 --version", "python"), ("uname -a", "os")]:
        try:
            r = __import__("subprocess").run(cmd.split(), capture_output=True, text=True, timeout=5)
            manifest[key] = r.stdout.strip()
        except: manifest[key] = "N/A"

    # Dependencies
    try:
        r = __import__("subprocess").run(["pip", "freeze"], capture_output=True, text=True, timeout=15)
        manifest["pip_hash"] = hashlib.sha256(r.stdout.encode()).hexdigest()[:16]
    except: manifest["pip_hash"] = "N/A"

    (BASELINE / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"  Baseline frozen: pip_hash={manifest['pip_hash']}")
    return manifest
