"""
BOCC Operational Intelligence Engine — Sprint 2
Additive only. Zero science changes. Backward compatible.

Modules:
  - MissionHealthEngine (0-100% composite health)
  - AnomalyDetector (severity-based)
  - RootCauseEngine (dependency tree)
  - RecommendationEngine (rule-based)
  - AlertCenter (UUID, severity, lifecycle)
  - MissionTimeline (chronological events)
  - Scorecard (component scores + trend)
  - SystemMap (dependency graph)
"""
import json, os, time, uuid, math
from pathlib import Path
from datetime import datetime, timezone, timedelta
from collections import deque, defaultdict

# ── Paths ───────────────────────────────────────────────
PDAC = Path("/opt/pimes/laws/runtime/validation/pdac")
RDMC = Path("/opt/pimes/laws/runtime/validation/rdmc")
BURNIN = Path("/opt/pimes/laws/runtime/validation/burnin")
PSEP = Path("/opt/pimes/laws/runtime/validation/psep")

OIE_DIR = PDAC / "operational_intelligence"
os.makedirs(OIE_DIR, exist_ok=True)

# ── Weights ─────────────────────────────────────────────
DEFAULT_WEIGHTS = {
    "collector": 0.20,
    "runtime": 0.20,
    "scientific": 0.20,
    "burnin": 0.12,
    "psep": 0.12,
    "governance": 0.06,
    "release": 0.05,
    "shadow": 0.05,
}

# ── Severity Levels ────────────────────────────────────
SEVERITY_ORDER = ["CRITICAL", "HIGH", "WARNING", "INFO"]

# ── Mission Health Engine ───────────────────────────────
class MissionHealthEngine:
    """Composite health 0-100%. Reads live system state. No computation."""
    
    def __init__(self, weights: dict = None):
        self.weights = weights or DEFAULT_WEIGHTS
        self.history = deque(maxlen=1440)  # 24h at 1min
    
    def compute(self) -> dict:
        scores = {}
        breakdown = {}
        
        # Collector score
        mf = PDAC / "collector_manifest.json"
        if mf.exists():
            try:
                d = json.loads(mf.read_text())
                q = d.get("queue", {})
                success = q.get("SUCCESS", 0)
                total = success + q.get("FAILED", 0) + q.get("RETRY", 0)
                collector_health = (success / max(total, 1)) * 100 if total > 0 else 80
                # Penalize if paused or stopped
                status = d.get("status", "")
                if status == "paused":
                    collector_health *= 0.7
                elif status != "running":
                    collector_health *= 0.5
                scores["collector"] = round(collector_health, 1)
                breakdown["collector"] = {"score": scores["collector"], "status": status}
            except:
                scores["collector"] = 0
        else:
            scores["collector"] = 50
        
        # Runtime score
        try:
            rdmc_log = RDMC / "rdmc.log"
            if rdmc_log.exists():
                log_age = time.time() - rdmc_log.stat().st_mtime
                runtime_score = 100 if log_age < 600 else max(0, 100 - (log_age - 600) / 60)
            else:
                runtime_score = 0
            scores["runtime"] = round(min(runtime_score, 100), 1)
            breakdown["runtime"] = {"score": scores["runtime"]}
        except:
            scores["runtime"] = 0
        
        # Scientific score
        try:
            s = json.loads((PSEP / "reports" / "SCIENTIFIC_SCORE.json").read_text())
            scores["scientific"] = round(s.get("score", 0) * 100, 1)
            breakdown["scientific"] = {"score": scores["scientific"], "verdict": s.get("verdict", "")}
        except:
            # Fallback: compute from stage artifacts
            legacy = list((PSEP / "dual_execution/legacy/stages").glob("*/*.npy"))
            runtime = list((PSEP / "dual_execution/runtime/stages").glob("*/*.npy"))
            if legacy and runtime:
                scores["scientific"] = 85.0  # baseline if artifacts exist
            else:
                scores["scientific"] = 0
            breakdown["scientific"] = {"score": scores["scientific"]}
        
        # Burn-in score
        bi_runs = BURNIN / "runs"
        if bi_runs.exists():
            try:
                runs = sorted(bi_runs.iterdir())
                if runs:
                    last = json.loads((runs[-1] / "result.json").read_text())
                    scores["burnin"] = round(last.get("score", 0) * 100, 1)
                    breakdown["burnin"] = {"score": scores["burnin"], "cycle": runs[-1].name}
                else:
                    scores["burnin"] = 0
                    breakdown["burnin"] = {"score": 0}
            except:
                scores["burnin"] = 50
                breakdown["burnin"] = {"score": 50}
        else:
            scores["burnin"] = 0
            breakdown["burnin"] = {"score": 0}
        
        # PSEP score (same as scientific for now)
        scores["psep"] = scores["scientific"]
        breakdown["psep"] = {"score": scores["psep"]}
        
        # Governance score
        idx = OIE_DIR / "index.json"
        gov_score = 100
        if idx.exists():
            try:
                cmds = json.loads(idx.read_text())
                if cmds:
                    failed = sum(1 for c in cmds.values() if c.get("state") == "FAILED")
                    total = len(cmds)
                    gov_score = ((total - failed) / total) * 100
            except: pass
        scores["governance"] = round(gov_score, 1)
        breakdown["governance"] = {"score": scores["governance"]}
        
        # Release score
        scores["release"] = 75.0  # RC1 baseline
        breakdown["release"] = {"score": scores["release"], "gate": "RC1 Candidate"}
        
        # Shadow score
        scores["shadow"] = 50.0  # Not started
        breakdown["shadow"] = {"score": scores["shadow"]}
        
        # Weighted composite
        total_weight = sum(self.weights.get(k, 0) for k in scores)
        composite = sum(scores.get(k, 0) * self.weights.get(k, 0) for k in scores)
        composite = composite / max(total_weight, 0.01)
        composite = max(0, min(100, composite))
        
        now = datetime.now(timezone.utc).isoformat()
        result = {
            "score": round(composite, 2),
            "components": scores,
            "breakdown": breakdown,
            "weights": self.weights,
            "status": "HEALTHY" if composite >= 80 else "DEGRADED" if composite >= 50 else "CRITICAL",
            "timestamp": now,
        }
        
        # Save history
        self.history.append({"timestamp": now, "score": composite})
        try:
            (OIE_DIR / "mission_health.json").write_text(json.dumps(result, indent=2, default=str))
            (OIE_DIR / "health_history.json").write_text(json.dumps(list(self.history), default=str))
        except: pass
        
        return result


# ── Anomaly Detector ────────────────────────────────────
class AnomalyDetector:
    """Detects system anomalies from live state."""
    
    def check(self) -> list:
        anomalies = []
        
        # 1. Collector queue growth
        mf = PDAC / "collector_manifest.json"
        if mf.exists():
            try:
                d = json.loads(mf.read_text())
                q = d.get("queue", {})
                retry = q.get("RETRY", 0)
                failed = q.get("FAILED", 0)
                waiting = q.get("WAITING", 0)
                
                if retry > 100:
                    anomalies.append({
                        "uuid": str(uuid.uuid4())[:8],
                        "severity": "HIGH",
                        "component": "collector",
                        "title": "High retry queue",
                        "description": f"Retry queue at {retry} items",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                if failed > 10:
                    anomalies.append({
                        "uuid": str(uuid.uuid4())[:8],
                        "severity": "WARNING",
                        "component": "collector",
                        "title": "Download failures detected",
                        "description": f"{failed} failed downloads",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
                if waiting > 500:
                    anomalies.append({
                        "uuid": str(uuid.uuid4())[:8],
                        "severity": "WARNING",
                        "component": "collector",
                        "title": "Download queue backlog",
                        "description": f"Waiting queue at {waiting}",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
            except: pass
        
        # 2. Scheduler process check
        try:
            import subprocess
            r = subprocess.run(["ps", "aux"], capture_output=True, text=True, timeout=5)
            if "_run_scheduler" not in r.stdout and "CollectorScheduler" not in r.stdout:
                anomalies.append({
                    "uuid": str(uuid.uuid4())[:8],
                    "severity": "CRITICAL",
                    "component": "collector",
                    "title": "Scheduler not running",
                    "description": "Collector scheduler process not found",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
        except: pass
        
        # 3. Runtime latency
        rdmc_log = RDMC / "rdmc.log"
        if rdmc_log.exists():
            try:
                age = time.time() - rdmc_log.stat().st_mtime
                if age > 3600:
                    anomalies.append({
                        "uuid": str(uuid.uuid4())[:8],
                        "severity": "HIGH",
                        "component": "runtime",
                        "title": "Runtime stale",
                        "description": f"No runtime activity for {age/60:.0f}min",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                    })
            except: pass
        
        # 4. Memory from burn-in
        bi_runs = BURNIN / "runs"
        if bi_runs.exists():
            try:
                runs = sorted(bi_runs.iterdir())
                if len(runs) >= 3:
                    mem_vals = []
                    for r in runs[-3:]:
                        res = json.loads((r / "result.json").read_text())
                        mem_vals.append(res.get("memory_mb", 0))
                    if len(mem_vals) >= 3 and all(mem_vals):
                        # Check for growth
                        if mem_vals[-1] > mem_vals[0] * 1.5:
                            anomalies.append({
                                "uuid": str(uuid.uuid4())[:8],
                                "severity": "HIGH",
                                "component": "burnin",
                                "title": "Possible memory leak",
                                "description": f"Memory: {mem_vals[0]:.0f} → {mem_vals[-1]:.0f} MB",
                                "timestamp": datetime.now(timezone.utc).isoformat(),
                            })
            except: pass
        
        return anomalies


# ── Root Cause Engine ───────────────────────────────────
class RootCauseEngine:
    """Builds dependency tree for anomalies."""
    
    DEPENDENCY_TREE = {
        "mission_health": ["collector", "runtime", "scientific", "burnin", "psep", "governance", "release"],
        "collector": ["scheduler", "sftp", "queue", "download", "validation"],
        "runtime": ["reader", "pc3", "tensor", "inference", "evidence", "fusion"],
        "scientific": ["runtime", "psep", "burnin"],
        "scheduler": ["worker_discovery", "worker_download", "worker_validation", "worker_runtime", "worker_audit"],
    }
    
    def trace(self, component: str) -> dict:
        """Build dependency tree for a component."""
        def _build(node):
            children = self.DEPENDENCY_TREE.get(node, [])
            return {
                "name": node,
                "status": self._get_status(node),
                "children": [_build(c) for c in children]
            }
        return _build(component)
    
    def _get_status(self, component: str) -> str:
        """Quick status check for a component."""
        if component == "collector":
            mf = PDAC / "collector_manifest.json"
            if mf.exists():
                try: return json.loads(mf.read_text()).get("status", "UNKNOWN")
                except: return "ERROR"
        return "UNKNOWN"


# ── Recommendation Engine ───────────────────────────────
class RecommendationEngine:
    RULES = {
        "collector_queue_high": {
            "condition": lambda a: a.get("title", "").startswith("High retry"),
            "actions": [
                "Check remote server connectivity",
                "Verify FTP/SFTP credentials",
                "Retry failed downloads from dashboard",
                "Consider increasing download interval",
            ]
        },
        "scheduler_not_running": {
            "condition": lambda a: "Scheduler not running" in a.get("title", ""),
            "actions": [
                "Restart scheduler from Governance Center",
                "Check system logs for crash reason",
                "Verify Python environment",
                "Check disk space",
            ]
        },
        "runtime_stale": {
            "condition": lambda a: "Runtime stale" in a.get("title", ""),
            "actions": [
                "Check runtime process status",
                "Verify pipeline is not blocked",
                "Restart runtime pipeline",
                "Check inference queue",
            ]
        },
        "memory_leak": {
            "condition": lambda a: "memory leak" in a.get("title", "").lower(),
            "actions": [
                "Monitor memory usage trend",
                "Restart pipeline if threshold exceeded",
                "Check for file descriptor leak",
                "Verify no thread accumulation",
            ]
        },
    }
    
    def recommend(self, anomaly: dict) -> list:
        for rule in self.RULES.values():
            if rule["condition"](anomaly):
                return rule["actions"]
        return ["Investigate anomaly in " + anomaly.get("component", "system")]


# ── Alert Center ────────────────────────────────────────
class AlertCenter:
    """Persistent alert management with lifecycle."""
    
    def __init__(self):
        self.alerts = []
        self._load()
    
    def _load(self):
        ap = OIE_DIR / "alerts.json"
        if ap.exists():
            try: self.alerts = json.loads(ap.read_text())
            except: self.alerts = []
    
    def _save(self):
        (OIE_DIR / "alerts.json").write_text(
            json.dumps(self.alerts[-500:], indent=2, default=str))
    
    def ingest(self, anomalies: list):
        """Add new anomalies as alerts, dedup by title+component."""
        existing = {(a.get("title"), a.get("component")) for a in self.alerts
                    if a.get("status") not in ("RESOLVED",)}
        for a in anomalies:
            key = (a.get("title"), a.get("component"))
            if key not in existing:
                a["status"] = "OPEN"
                a["acknowledged"] = False
                a["resolved_at"] = None
                self.alerts.append(a)
                existing.add(key)
        self._save()
    
    def acknowledge(self, alert_uuid: str):
        for a in self.alerts:
            if a.get("uuid") == alert_uuid:
                a["acknowledged"] = True
                a["status"] = "ACKNOWLEDGED"
                break
        self._save()
    
    def resolve(self, alert_uuid: str):
        for a in self.alerts:
            if a.get("uuid") == alert_uuid:
                a["status"] = "RESOLVED"
                a["resolved_at"] = datetime.now(timezone.utc).isoformat()
                break
        self._save()
    
    def list(self, severity: str = None, component: str = None, limit: int = 100) -> list:
        results = self.alerts
        if severity:
            results = [a for a in results if a.get("severity") == severity]
        if component:
            results = [a for a in results if a.get("component") == component]
        return sorted(results, key=lambda a: a.get("timestamp", ""), reverse=True)[:limit]
    
    def count_by_severity(self) -> dict:
        counts = {"CRITICAL": 0, "HIGH": 0, "WARNING": 0, "INFO": 0}
        for a in self.alerts:
            if a.get("status") not in ("RESOLVED",):
                sev = a.get("severity", "INFO")
                if sev in counts: counts[sev] += 1
        return counts


# ── Mission Timeline ────────────────────────────────────
class MissionTimeline:
    """Chronological event log for all components."""
    
    def __init__(self):
        self.events = deque(maxlen=1000)
        self._load()
    
    def _load(self):
        tp = OIE_DIR / "timeline.json"
        if tp.exists():
            try: self.events = deque(json.loads(tp.read_text()), maxlen=1000)
            except: pass
    
    def _save(self):
        (OIE_DIR / "timeline.json").write_text(
            json.dumps(list(self.events), indent=2, default=str))
    
    def add(self, component: str, event: str, detail: str = ""):
        entry = {
            "uuid": str(uuid.uuid4())[:8],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "wita": (datetime.now(timezone.utc) + timedelta(hours=8)).strftime("%H:%M:%S"),
            "component": component,
            "event": event,
            "detail": detail,
        }
        self.events.append(entry)
        self._save()
    
    def list(self, component: str = None, limit: int = 50) -> list:
        results = list(self.events)
        if component:
            results = [e for e in results if e.get("component") == component]
        return results[-limit:]


# ── Scorecard ───────────────────────────────────────────
class Scorecard:
    """Component scores with trend direction."""
    
    def score(self, health: dict) -> dict:
        now = datetime.now(timezone.utc).isoformat()
        components = health.get("components", {})
        
        # Load previous for trend
        prev = None
        hp = OIE_DIR / "previous_scorecard.json"
        if hp.exists():
            try: prev = json.loads(hp.read_text())
            except: pass
        
        result = {}
        for name, score in components.items():
            trend = "→"
            if prev and name in prev:
                diff = score - prev[name]
                trend = "↑" if diff > 1 else "↓" if diff < -1 else "→"
            result[name] = {"score": score, "trend": trend}
        
        # Save
        (OIE_DIR / "previous_scorecard.json").write_text(json.dumps(components, default=str))
        
        return {
            "components": result,
            "overall": health.get("score", 0),
            "timestamp": now,
        }


# ── System Map ──────────────────────────────────────────
class SystemMap:
    """Dependency graph with live status colors."""
    
    NODES = [
        {"id": "collector", "label": "Collector", "depends_on": []},
        {"id": "validation", "label": "Validation", "depends_on": ["collector"]},
        {"id": "reader", "label": "Reader", "depends_on": ["validation"]},
        {"id": "pc3", "label": "PC3", "depends_on": ["reader"]},
        {"id": "tensor", "label": "Tensor", "depends_on": ["pc3"]},
        {"id": "inference", "label": "Inference", "depends_on": ["tensor"]},
        {"id": "evidence", "label": "Evidence", "depends_on": ["inference"]},
        {"id": "fusion", "label": "Fusion", "depends_on": ["evidence"]},
        {"id": "burnin", "label": "Burn-in", "depends_on": ["fusion"]},
        {"id": "psep", "label": "PSEP", "depends_on": ["burnin"]},
        {"id": "release", "label": "Release", "depends_on": ["psep"]},
        {"id": "dashboard", "label": "Dashboard", "depends_on": ["release"]},
    ]
    
    def build(self, health: dict) -> list:
        """Return nodes with current status colors."""
        components = health.get("components", {})
        
        def score_to_color(score):
            if score >= 80: return "green"
            if score >= 60: return "yellow"
            if score >= 40: return "orange"
            return "red"
        
        result = []
        for node in self.NODES:
            nid = node["id"]
            score = components.get(nid, 50)
            result.append({
                "id": nid,
                "label": node["label"],
                "depends_on": node["depends_on"],
                "score": score,
                "color": score_to_color(score),
            })
        return result


# ── Singleton instances ─────────────────────────────────
health_engine = MissionHealthEngine()
anomaly_detector = AnomalyDetector()
root_cause_engine = RootCauseEngine()
recommendation_engine = RecommendationEngine()
alert_center = AlertCenter()
mission_timeline = MissionTimeline()
scorecard = Scorecard()
system_map = SystemMap()


# ── Tick — called periodically ──────────────────────────
def tick():
    """Run all engines and return combined state."""
    health = health_engine.compute()
    anomalies = anomaly_detector.check()
    alert_center.ingest(anomalies)
    sc = scorecard.score(health)
    sm = system_map.build(health)
    
    return {
        "health": health,
        "anomalies": anomalies,
        "alerts": alert_center.count_by_severity(),
        "scorecard": sc,
        "system_map": sm,
    }
