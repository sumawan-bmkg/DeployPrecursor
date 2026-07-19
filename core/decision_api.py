"""Decision API — structured operational decision output."""
import json, uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, Optional


@dataclass
class OperationalDecision:
    alert: bool = False
    alert_level: str = "none"
    magnitude_estimate: float = 0.0
    confidence: float = 0.0
    reason: str = ""
    risk_score: float = 0.0
    recommendation: str = ""
    feature_values: Dict[str, float] = field(default_factory=dict)
    model_output: float = 0.0
    threshold: float = 0.0
    timestamp: str = ""
    decision_id: str = ""
    
    def __post_init__(self):
        if not self.timestamp: self.timestamp = datetime.now().isoformat()
        if not self.decision_id: self.decision_id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> dict: return asdict(self)
    def to_json(self) -> str: return json.dumps(self.to_dict(), indent=2)


class DecisionEngine:
    def __init__(self, alert_threshold: float = 0.5, watch_threshold: float = 0.3):
        self.alert_threshold = alert_threshold
        self.watch_threshold = watch_threshold
    
    def decide(self, model_output: float,
               feature_context: Optional[Dict] = None) -> OperationalDecision:
        d = OperationalDecision(model_output=model_output, threshold=self.alert_threshold,
                                feature_values=feature_context or {})
        
        if model_output >= self.alert_threshold:
            d.alert = True
            d.alert_level = "alert"
            d.recommendation = "ISSUE ALERT — notify BMKG operator"
        elif model_output >= self.watch_threshold:
            d.alert_level = "warning"
            d.recommendation = "INCREASE MONITORING — prepare for potential alert"
        else:
            d.recommendation = "NO ACTION — continue routine monitoring"
        
        d.confidence = round(min(1.0, abs(model_output - 0.5) * 4), 3)
        d.risk_score = round(model_output, 3)
        
        if feature_context:
            top = sorted(feature_context.items(), key=lambda x: -abs(x[1]))[:3]
            d.reason = f"Top: {', '.join(f'{k}={v:.3f}' for k, v in top)}"
        
        return d
    
    def explain_decision(self, d: OperationalDecision) -> str:
        return (f"Decision {d.decision_id}: alert={d.alert} ({d.alert_level}), "
                f"confidence={d.confidence:.1%}, risk={d.risk_score:.3f}\n"
                f"Reason: {d.reason}\nRecommendation: {d.recommendation}")
