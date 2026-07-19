"""OperationMetrics - Thread-safe health metric counters."""
from __future__ import annotations
import threading
import time
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class OperationMetrics:
    """Thread-safe operational metrics. Exposed via QCOrchestrator.get_metrics()."""
    qc_total: int = 0
    qc_pass: int = 0
    qc_fail: int = 0
    quarantine_count: int = 0
    rule_fail_count: int = 0
    total_duration_ms: float = 0.0
    average_score: float = 0.0
    last_timestamp: str = ""
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def record(self, passed: bool, duration_ms: float, score: float,
               rule_fails: int = 0, quarantined: bool = False):
        with self._lock:
            self.qc_total += 1
            if passed: self.qc_pass += 1
            else: self.qc_fail += 1
            self.total_duration_ms += duration_ms
            self.rule_fail_count += rule_fails
            self.average_score = self._rolling_avg(score)
            if quarantined: self.quarantine_count += 1
            self.last_timestamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    def _rolling_avg(self, new_score: float) -> float:
        if self.qc_total == 0: return new_score
        total = self.average_score * (self.qc_total - 1) + new_score
        return round(total / self.qc_total, 4)

    def snapshot(self) -> Dict:
        with self._lock:
            avg_dur = round(self.total_duration_ms / self.qc_total, 1) if self.qc_total > 0 else 0.0
            return {
                "qc_total": self.qc_total,
                "qc_pass": self.qc_pass,
                "qc_fail": self.qc_fail,
                "quarantine_count": self.quarantine_count,
                "rule_fail_count": self.rule_fail_count,
                "average_score": self.average_score,
                "average_duration_ms": avg_dur,
                "pass_rate": round(self.qc_pass / self.qc_total, 4) if self.qc_total > 0 else 1.0,
                "last_timestamp": self.last_timestamp,
            }
