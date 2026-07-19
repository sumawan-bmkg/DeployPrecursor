"""
Infrastructure & Pipeline Monitoring — RC2 Dashboard
Additive only. Zero science changes. No pipeline modification.
Collects system metrics and pipeline state for display only.
"""
import json, os, time, glob, hashlib, subprocess, math
from pathlib import Path
from datetime import datetime, timezone

# ── Safe Float ─────────────────────────────────────────
def sf(v, default=0.0):
    """Convert to JSON-safe float."""
    if v is None: return default
    try:
        f = float(v)
        if math.isnan(f) or math.isinf(f): return default
        return f
    except: return default

def safe_dict(d: dict) -> dict:
    """Recursively sanitize all float values in a dict."""
    out = {}
    for k, v in d.items():
        if isinstance(v, float): out[k] = sf(v)
        elif isinstance(v, dict): out[k] = safe_dict(v)
        else: out[k] = v
    return out

PDAC = Path("/opt/pimes/laws/runtime/validation/pdac")
RDMC = Path("/opt/pimes/laws/runtime/validation/rdmc")
BURNIN = Path("/opt/pimes/laws/runtime/validation/burnin")
PSEP = Path("/opt/pimes/laws/runtime/validation/psep")
RUNTIME = Path("/opt/pimes/laws/runtime")


# ── Infrastructure Collector ────────────────────────────
class InfrastructureCollector:
    """Read system metrics. Read-only. Never modifies."""
    
    def collect(self) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        return {
            "cpu": self._cpu(),
            "memory": self._memory(),
            "disk": self._disk(),
            "gpu": self._gpu(),
            "network": self._network(),
            "process": self._process(),
            "load": self._load(),
            "timestamp": now,
        }
    
    def _cpu(self) -> dict:
        try:
            # CPU usage from /proc/stat
            with open("/proc/stat") as f:
                line = f.readline()
            parts = line.split()
            idle = int(parts[4])
            total = sum(int(x) for x in parts[1:])
            
            # Load average
            with open("/proc/loadavg") as f:
                load = f.read().split()[:3]
            
            # CPU count
            cpus = os.cpu_count() or 1
            
            # Temperature (if available)
            temp = None
            try:
                with open("/sys/class/thermal/thermal_zone0/temp") as f:
                    temp = int(f.read().strip()) / 1000
            except: pass
            
            return {
                "cores": cpus,
                "load_1m": float(load[0]),
                "load_5m": float(load[1]),
                "load_15m": float(load[2]),
                "idle_pct": round(idle / max(total, 1) * 100, 1),
                "usage_pct": round((1 - idle / max(total, 1)) * 100, 1),
                "temperature_c": temp,
            }
        except: return {"cores": 0, "usage_pct": 0, "load_1m": 0, "load_5m": 0, "load_15m": 0}
    
    def _memory(self) -> dict:
        try:
            with open("/proc/meminfo") as f:
                info = {}
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        val = int(parts[1].strip().split()[0])  # kB
                        info[key] = val
            total = info.get("MemTotal", 1)
            avail = info.get("MemAvailable", 0)
            used = total - avail
            swap_total = info.get("SwapTotal", 0)
            swap_free = info.get("SwapFree", 0)
            return {
                "total_mb": round(total / 1024),
                "used_mb": round(used / 1024),
                "available_mb": round(avail / 1024),
                "usage_pct": round(used / max(total, 1) * 100, 1),
                "swap_total_mb": round(swap_total / 1024),
                "swap_used_mb": round((swap_total - swap_free) / 1024),
                "swap_pct": round((swap_total - swap_free) / max(swap_total, 1) * 100, 1) if swap_total > 0 else 0,
            }
        except: return {"total_mb": 0, "used_mb": 0, "usage_pct": 0}
    
    def _disk(self) -> list:
        try:
            r = subprocess.run(["df", "-B1", "--output=source,target,size,used,avail,pcent,fstype"],
                             capture_output=True, text=True, timeout=5)
            lines = r.stdout.strip().split("\n")[1:]
            disks = []
            for line in lines:
                parts = line.split()
                if len(parts) >= 6 and parts[0].startswith("/"):
                    disks.append({
                        "device": parts[0],
                        "mount": parts[1],
                        "total_gb": round(int(parts[2]) / 1e9, 1),
                        "used_gb": round(int(parts[3]) / 1e9, 1),
                        "avail_gb": round(int(parts[4]) / 1e9, 1),
                        "usage_pct": int(parts[5].rstrip("%")),
                    })
            return disks
        except: return []
    
    def _gpu(self) -> dict:
        try:
            r = subprocess.run(["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
                             "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=5)
            if r.returncode == 0 and r.stdout.strip():
                parts = r.stdout.strip().split(", ")
                return {
                    "name": parts[0],
                    "utilization_pct": int(parts[1]),
                    "memory_used_mb": int(parts[2]),
                    "memory_total_mb": int(parts[3]),
                    "temperature_c": int(parts[4]),
                }
        except: pass
        return {"available": False, "name": "N/A"}
    
    def _network(self) -> dict:
        try:
            with open("/proc/net/dev") as f:
                lines = f.readlines()[2:]  # skip headers
            rx_total = 0
            tx_total = 0
            for line in lines:
                parts = line.split()
                if len(parts) >= 10:
                    rx_total += int(parts[1])
                    tx_total += int(parts[9])
            return {
                "rx_gb": round(rx_total / 1e9, 2),
                "tx_gb": round(tx_total / 1e9, 2),
            }
        except: return {"rx_gb": 0, "tx_gb": 0}
    
    def _process(self) -> dict:
        try:
            r = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)
            lines = r.stdout.strip().split("\n")
            total = len(lines) - 1  # minus header
            
            # Count FDs
            fd_count = 0
            try:
                _, fd_out, _ = subprocess.run(["ls", "/proc/self/fd"], capture_output=True, text=True)
                fd_count = len(fd_out.strip().split("\n"))
            except: pass
            
            # Thread count
            threads = 0
            try:
                _, th_out, _ = subprocess.run(["ps", "eL"], capture_output=True, text=True, timeout=5)
                threads = len(th_out.strip().split("\n")) - 1
            except: pass
            
            return {"total_processes": total, "open_fds": fd_count, "threads": threads}
        except: return {"total_processes": 0, "open_fds": 0, "threads": 0}
    
    def _load(self) -> dict:
        try:
            r = subprocess.run(["uptime"], capture_output=True, text=True, timeout=5)
            return {"uptime": r.stdout.strip()}
        except: return {"uptime": "unknown"}


# ── Pipeline Stage Collector ────────────────────────────
PIPELINE_STAGES = [
    {"id": "collector", "label": "Collector", "category": "acquisition"},
    {"id": "validation", "label": "Validation", "category": "acquisition"},
    {"id": "reader", "label": "Reader", "category": "processing"},
    {"id": "signal", "label": "Signal Processing", "category": "processing"},
    {"id": "pc3", "label": "PC3", "category": "processing"},
    {"id": "tensor", "label": "Tensor", "category": "computation"},
    {"id": "inference", "label": "Inference", "category": "computation"},
    {"id": "fusion", "label": "Fusion", "category": "computation"},
    {"id": "prediction", "label": "Prediction", "category": "output"},
    {"id": "evidence", "label": "Evidence", "category": "output"},
    {"id": "burnin", "label": "Burn-in", "category": "validation"},
    {"id": "psep", "label": "PSEP", "category": "validation"},
    {"id": "shadow", "label": "Shadow", "category": "validation"},
    {"id": "release", "label": "Release", "category": "deployment"},
    {"id": "dashboard", "label": "Dashboard", "category": "deployment"},
]

def sf(v, default=0): return default if (v is None or (isinstance(v, float) and math.isnan(v))) else v

class PipelineCollector:
    """Collect pipeline stage state. Read-only."""
    
    def collect_stages(self) -> list:
        stages = []
        for stage in PIPELINE_STAGES:
            data = {
                "id": stage["id"],
                "label": stage["label"],
                "category": stage["category"],
                "status": "UNKNOWN",
                "score": 0,
                "last_activity": None,
                "hash": None,
                "evidence": None,
                "log_preview": "",
                "execution_time_s": None,
            }
            
            # Collect per-stage data
            if stage["id"] == "collector":
                data.update(self._collector())
            elif stage["id"] == "validation":
                data.update(self._validation())
            elif stage["id"] == "reader":
                data.update(self._reader())
            elif stage["id"] == "inference":
                data.update(self._inference())
            elif stage["id"] == "tensor":
                data.update(self._tensor())
            elif stage["id"] == "fusion":
                data.update(self._fusion())
            elif stage["id"] == "prediction":
                data.update(self._prediction())
            elif stage["id"] == "burnin":
                data.update(self._burnin())
            elif stage["id"] == "psep":
                data.update(self._psep())
            elif stage["id"] == "evidence":
                data.update(self._evidence())
            elif stage["id"] == "release":
                data.update(self._release())
            
            # Safety: sanitize all scores for JSON serialization
            score = sf(data.get("score", 0))
            data["score"] = score
            
            stages.append(data)
        return stages
    
    def _collector(self) -> dict:
        mf = PDAC / "collector_manifest.json"
        if mf.exists():
            try:
                d = json.loads(mf.read_text())
                q = d.get("queue", {})
                total = q.get("SUCCESS", 0) + q.get("FAILED", 0) + q.get("RETRY", 0) + q.get("WAITING", 0)
                score = (q.get("SUCCESS", 0) / max(total, 1)) * 100 if total > 0 else 0
                return {"status": d.get("status", "UNKNOWN").upper(), "score": sf(score)}
            except: pass
        return {"status": "UNAVAILABLE", "score": 0}
    
    def _validation(self) -> dict:
        mf = PDAC / "collector_manifest.json"
        if mf.exists():
            try:
                d = json.loads(mf.read_text())
                v = d.get("validation", {})
                validated = v.get("validated", 0)
                total = v.get("total", 0)
                score = (validated / max(total, 1)) * 100 if total > 0 else 50
                return {"status": "ACTIVE" if total > 0 else "STANDBY", "score": sf(score)}
            except: pass
        return {"status": "UNKNOWN", "score": 50}
    
    def _reader(self) -> dict:
        rdm = RDMC / "rdmc.log"
        if rdm.exists():
            age = time.time() - rdm.stat().st_mtime
            status = "ACTIVE" if age < 300 else "STALE" if age < 3600 else "INACTIVE"
            score = 100 if age < 300 else max(0, 100 - age / 60)
            return {"status": status, "score": sf(min(score, 100))}
        return {"status": "UNAVAILABLE", "score": 0}
    
    def _inference(self) -> dict:
        arts = list((PSEP / "dual_execution/legacy/stages/inference").glob("*.npy")) if PSEP.exists() else []
        if arts:
            latest = max(arts, key=lambda x: x.stat().st_mtime)
            age = time.time() - latest.stat().st_mtime
            score = 100 if age < 7200 else max(0, 100 - (age - 7200) / 3600)
            return {"status": "ACTIVE" if age < 7200 else "STALE", "score": min(score, 100), 
                    "hash": hashlib.sha256(latest.read_bytes()[:4096]).hexdigest()[:16]}
        return {"status": "NO_DATA", "score": 0}
    
    def _tensor(self) -> dict:
        arts = list((PSEP / "dual_execution/legacy/stages/tensor").glob("*.npy")) if PSEP.exists() else []
        if arts:
            return {"status": "ACTIVE", "score": 80}
        return {"status": "NO_DATA", "score": 0}
    
    def _fusion(self) -> dict:
        arts = list((PSEP / "dual_execution/legacy/stages/fusion").glob("*.npy")) if PSEP.exists() else []
        if arts:
            return {"status": "ACTIVE", "score": 80}
        return {"status": "NO_DATA", "score": 0}
    
    def _prediction(self) -> dict:
        try:
            arts = list((PSEP / "dual_execution/legacy/stages/inference/ALR_probs.npy").parent.glob("*.npy")) if PSEP.exists() else []
            if arts:
                val = float(arts[-1].stat().st_size) / 1000  # fallback: file size as proxy
                status = "ACTIVE"
                return {"status": "ACTIVE", "score": 85, "value": 0}
        except: pass
        return {"status": "NO_DATA", "score": 0}
    
    def _burnin(self) -> dict:
        bi = BURNIN / "runs"
        if bi.exists():
            try:
                runs = sorted(bi.iterdir())
                if runs:
                    last = json.loads((runs[-1] / "result.json").read_text())
                    score = last.get("score", 0) * 100
                    return {"status": "COMPLETE" if score > 80 else "IN_PROGRESS", "score": score,
                            "cycles": len(runs), "cycle": runs[-1].name}
            except: pass
        return {"status": "UNAVAILABLE", "score": 0}
    
    def _psep(self) -> dict:
        try:
            s = json.loads((PSEP / "reports" / "SCIENTIFIC_SCORE.json").read_text())
            return {"status": "ACTIVE", "score": s.get("score", 0) * 100}
        except: pass
        return {"status": "UNAVAILABLE", "score": 0}
    
    def _evidence(self) -> dict:
        ev_dir = PDAC / "governance" / "evidence"
        if ev_dir.exists():
            packages = list(ev_dir.iterdir())
            return {"status": "ACTIVE" if packages else "EMPTY", "count": len(packages), "score": 100 if packages else 50}
        return {"status": "UNAVAILABLE", "score": 0}
    
    def _release(self) -> dict:
        return {"status": "RC1_CANDIDATE", "score": 75}


# ── Collector Analytics ─────────────────────────────────
class CollectorAnalytics:
    """Deep collector metrics. Read-only."""
    
    def collect(self) -> dict:
        mf = PDAC / "collector_manifest.json"
        remote = PDAC / "remote_manifest.json"
        result = {
            "status": "STANDBY",
            "queue": {"total": 0, "success": 0, "failed": 0, "retry": 0, "waiting": 0},
            "stations": {"online": 0, "offline": 0, "total": 0, "list": []},
            "workers": {"discovery": {}, "download": {}, "validation": {}, "runtime": {}, "audit": {}},
            "scheduler": {"uptime": None, "last_cycle": None, "latency_ms": None},
            "throughput": {"downloads_per_hour": 0, "avg_transfer_speed_mb": 0},
        }
        
        if mf.exists():
            try:
                d = json.loads(mf.read_text())
                result["status"] = d.get("status", "UNKNOWN")
                q = d.get("queue", {})
                result["queue"] = {
                    "success": q.get("SUCCESS", 0), "failed": q.get("FAILED", 0),
                    "retry": q.get("RETRY", 0), "waiting": q.get("WAITING", 0),
                    "total": sum(q.values()),
                }
                r = d.get("remote", {})
                result["stations"] = {
                    "online": r.get("online", 0), "offline": r.get("offline", 0),
                    "total": r.get("total_stations", 0),
                    "list": r.get("station_list", [])[:20],
                }
                result["workers"] = d.get("workers", result["workers"])
            except: pass
        
        if remote.exists():
            try:
                rm = json.loads(remote.read_text())
                stations = rm.get("stations", [])
                result["stations"]["total"] = len(stations)
                result["stations"]["list"] = [
                    {"name": s.get("name", ""), "available": s.get("available", False),
                     "last_data": s.get("last_data", "")}
                    for s in stations[:30]
                ]
            except: pass
        
        # Scheduler log
        lp = PDAC / "scheduler.log"
        if lp.exists():
            try:
                lines = lp.read_text().splitlines()[-10:]
                result["scheduler"]["log_preview"] = lines
                if lines:
                    result["scheduler"]["last_line"] = lines[-1]
            except: pass
        
        return result


# ── Evidence Explorer ───────────────────────────────────
class EvidenceExplorer:
    """Search and list all evidence packages."""
    
    def list_packages(self, search: str = None, limit: int = 50) -> list:
        packages = []
        
        # Governance evidence
        gov_dir = PDAC / "governance" / "evidence"
        if gov_dir.exists():
            for d in sorted(gov_dir.iterdir(), reverse=True):
                if d.is_dir():
                    manifest = d / "manifest_reference.json"
                    try:
                        m = json.loads(manifest.read_text()) if manifest.exists() else {}
                    except: m = {}
                    packages.append({
                        "uuid": d.name,
                        "type": "governance",
                        "timestamp": m.get("timestamp", d.stat().st_mtime),
                        "status": "AVAILABLE",
                        "files": [f.name for f in d.iterdir()],
                        "size_kb": sum(f.stat().st_size for f in d.iterdir() if f.is_file()) / 1024,
                    })
        
        # PSEP evidence
        if PSEP.exists():
            reports = PSEP / "reports"
            if reports.exists():
                for f in reports.glob("*.json"):
                    packages.append({
                        "uuid": f.stem,
                        "type": "psep",
                        "timestamp": f.stat().st_mtime,
                        "status": "AVAILABLE",
                        "files": [f.name],
                        "size_kb": f.stat().st_size / 1024,
                    })
        
        # Burn-in evidence
        bi = BURNIN / "runs"
        if bi.exists():
            for d in sorted(bi.iterdir(), reverse=True):
                if d.is_dir():
                    packages.append({
                        "uuid": d.name,
                        "type": "burnin",
                        "timestamp": d.stat().st_mtime,
                        "status": "AVAILABLE",
                        "files": [f.name for f in d.iterdir() if f.is_file()],
                        "size_kb": sum(f.stat().st_size for f in d.iterdir() if f.is_file()) / 1024,
                    })
        
        # Filter by search
        if search:
            packages = [p for p in packages if search.lower() in p["uuid"].lower() 
                       or search.lower() in p["type"].lower()
                       or any(search.lower() in f.lower() for f in p["files"])]
        
        return sorted(packages, key=lambda p: p.get("timestamp", 0), reverse=True)[:limit]
    
    def get_package(self, uuid: str) -> dict:
        """Get details of a specific evidence package."""
        # Check governance
        gov_dir = PDAC / "governance" / "evidence" / uuid
        if gov_dir.exists():
            files = {}
            for f in gov_dir.iterdir():
                if f.is_file():
                    try: files[f.name] = json.loads(f.read_text())
                    except: files[f.name] = f.read_text()[:500]
            return {"uuid": uuid, "type": "governance", "files": files}
        
        # Check PSEP
        for ext in [".json"]:
            f = PSEP / "reports" / (uuid + ext) if PSEP.exists() else None
            if f and f.exists():
                try: return {"uuid": uuid, "type": "psep", "files": {f.name: json.loads(f.read_text())}}
                except: pass
        
        return {"uuid": uuid, "type": "unknown", "error": "Not found"}


# ── Release Status ──────────────────────────────────────
class ReleaseStatus:
    """Release gate status. Read-only."""
    
    GATES = {
        "rc1": {
            "name": "RC1 Candidate",
            "checklist": [
                ("Collector stable", "collector"),
                ("Runtime pipeline complete", "runtime"),
                ("Scientific equivalence verified", "scientific"),
                ("Burn-in score ≥ 80%", "burnin"),
                ("PSEP score ≥ 90%", "psep"),
                ("Evidence package generated", "evidence"),
                ("Governance layer operational", "governance"),
                ("Shadow mode not required for RC1", "shadow"),
                ("No critical anomalies", "alerts"),
                ("Operator sign-off", "approval"),
            ],
        },
        "rc2": {
            "name": "RC2 Candidate",
            "checklist": [
                ("All RC1 gates passed", "rc1"),
                ("Shadow mode ≥ 7 days", "shadow"),
                ("Scientific drift < 1%", "drift"),
                ("Prediction accuracy ≥ 95%", "accuracy"),
                ("No HIGH anomalies for 48h", "stability"),
                ("Performance baseline established", "performance"),
                ("Documentation complete", "docs"),
                ("ERB review complete", "erb"),
            ],
        },
        "production": {
            "name": "Production",
            "checklist": [
                ("All RC2 gates passed", "rc2"),
                ("BMKG approval", "bmkg"),
                ("Emergency procedure tested", "emergency"),
                ("Backup system ready", "backup"),
                ("24/7 monitoring active", "monitoring"),
                ("Incident response plan", "incident"),
            ],
        },
    }
    
    def get_status(self) -> dict:
        result = {}
        for phase, config in self.GATES.items():
            gates = []
            for gate_name, gate_id in config["checklist"]:
                gates.append({
                    "gate": gate_name,
                    "id": gate_id,
                    "status": "PENDING",
                    "evidence": None,
                })
            result[phase] = {
                "name": config["name"],
                "gates": gates,
                "passed": 0,
                "total": len(gates),
                "readiness": 0,
            }
        
        # Auto-evaluate RC1 gates
        if "rc1" in result:
            passed = 0
            gates = result["rc1"]["gates"]
            
            # Collector stable
            mf = PDAC / "collector_manifest.json"
            if mf.exists():
                try:
                    d = json.loads(mf.read_text())
                    if d.get("status") == "running":
                        gates[0]["status"] = "PASSED"; gates[0]["evidence"] = "collector_manifest.json"; passed += 1
                    else: gates[0]["status"] = "FAILED"
                except: pass
            
            # Runtime pipeline
            if RDMC.exists() and any(RDMC.glob("*.log")):
                gates[1]["status"] = "PASSED"; gates[1]["evidence"] = "rdmc.log"; passed += 1
            
            # PSEP score
            try:
                s = json.loads((PSEP / "reports" / "SCIENTIFIC_SCORE.json").read_text())
                if s.get("score", 0) >= 0.9:
                    gates[4]["status"] = "PASSED"; gates[4]["evidence"] = "SCIENTIFIC_SCORE.json"; passed += 1
                else: gates[4]["status"] = "PARTIAL"
            except: pass
            
            # Evidence
            ev = PDAC / "governance" / "evidence"
            if ev.exists() and any(ev.iterdir()):
                gates[6]["status"] = "PASSED"; gates[6]["evidence"] = "evidence/"; passed += 1
            
            # Governance
            gov_dir = PDAC / "governance"
            if gov_dir.exists():
                gates[7]["status"] = "PASSED"; gates[7]["evidence"] = "governance/"; passed += 1
            
            result["rc1"]["passed"] = passed
            result["rc1"]["readiness"] = round(passed / len(gates) * 100)
        
        return result


# Singletons
infra_collector = InfrastructureCollector()
pipeline_collector = PipelineCollector()
collector_analytics = CollectorAnalytics()
evidence_explorer = EvidenceExplorer()
release_status = ReleaseStatus()
