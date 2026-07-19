"""MonitoringEngine — single engine for all operational metrics."""
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
from .evaluator import UnifiedEvaluator
from .decision_api import OperationalDecision


class MonitoringEngine:
    def __init__(self):
        self.metrics_history: List[Dict] = []
        self.evaluator = UnifiedEvaluator()
    
    def compute_all(self, feature_values: Dict[str, List[float]],
                    target_values: List[float],
                    decisions: List[OperationalDecision]) -> Dict[str, Any]:
        feature_metrics = {}
        for fname, fvals in feature_values.items():
            try:
                feature_metrics[fname] = self.evaluator.evaluate(fvals, target_values)
            except Exception as e:
                feature_metrics[fname] = {"error": str(e)}
        
        tiis = [v.get("TII", 0) for v in feature_metrics.values() if "TII" in v]
        ouis = [v.get("OUI", 0) for v in feature_metrics.values() if "OUI" in v]
        rsis = [v.get("RSI_sensitivity", 0) for v in feature_metrics.values() if "RSI_sensitivity" in v]
        
        r = {
            "TII": round(np.mean(tiis), 2) if tiis else 0,
            "TII_max": round(max(tiis), 2) if tiis else 0,
            "OUI": round(np.mean(ouis), 2) if ouis else 0,
            "DIS": round(sum(1 for d in decisions if d.confidence > 0.7) / max(len(decisions), 1) * 100, 2),
            "DVI": round(sum(1 for v in feature_metrics.values() if "error" not in v) / max(len(feature_values), 1) * 100, 2),
            "RSI": round(np.mean(rsis), 3) if rsis else 0,
        }
        
        tii_n = min(1, r["TII"] / 100)
        oui_n = min(1, r["OUI"] / 100)
        dis_n = min(1, r["DIS"] / 100)
        dvi_n = min(1, r["DVI"] / 100)
        odri = (tii_n * 0.25 + oui_n * 0.25 + dis_n * 0.2 + dvi_n * 0.15 + r["RSI"] * 0.15) * 100
        r["ODRI"] = round(min(100, odri), 1)
        
        entry = {"timestamp": datetime.now().isoformat(), **r,
                 "feature_count": len(feature_values), "decision_count": len(decisions)}
        self.metrics_history.append(entry)
        return r
