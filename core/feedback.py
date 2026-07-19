"""
Operator Feedback Module — log, learn, improve from operator actions.
"""
import json, os, uuid
from datetime import datetime
from pathlib import Path
from collections import defaultdict

class FeedbackLogger:
    def __init__(self, log_dir=None):
        self.log_dir = Path(log_dir) if log_dir else Path("pilot/logs/feedback")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self._stats = defaultdict(int)

    def log(self, decision_id, operator_id, label,
            override_action="none", notes="", context=None):
        entry = {
            "decision_id": decision_id,
            "timestamp": datetime.now().isoformat(),
            "operator_id": operator_id,
            "label": label,
            "override_action": override_action,
            "notes": notes,
            "context": context or {},
        }
        date_str = datetime.now().strftime("%Y%m%d")
        log_file = self.log_dir / f"feedback_{date_str}.jsonl"
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
        self._stats[label] += 1
        self._stats["total"] += 1
        return entry

    def get_stats(self):
        return dict(self._stats)

    def get_false_alarm_rate(self, days=30):
        cutoff = datetime.now().timestamp() - days * 86400
        fas = 0
        total = 0
        for f in sorted(self.log_dir.glob("*.jsonl")):
            for line in f.read_text().strip().split("\n"):
                if not line: continue
                try:
                    e = json.loads(line)
                    total += 1
                    if e.get("label") == "wrong" and e.get("context", {}).get("actual_outcome") == 0:
                        fas += 1
                except:
                    pass
        return fas / max(total, 1)
