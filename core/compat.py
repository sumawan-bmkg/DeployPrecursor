"""
compat — Compatibility Layer for legacy pipeline scripts.

All adapters maintain the original function signatures for backward compatibility
while delegating to the new magbind.core/ API internally.

Usage:
    from core.compat import legacy_train, legacy_predict, legacy_feature
    # Same API as before, but runs through kernel now.
"""
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
import numpy as np
import pandas as pd

# Import kernel
from .registry import FeatureRegistry, FeatureRecord
from .evaluator import UnifiedEvaluator
from .feature_store import FeatureStore
from .model_api import create_model, BaseModel
from .decision_api import DecisionEngine, OperationalDecision
from .monitoring import MonitoringEngine


# ============================================================
# ADAPTER: Feature Extraction
# ============================================================

_registry = FeatureRegistry()
_store = FeatureStore()
_evaluator = UnifiedEvaluator()


def legacy_feature(name: str, compute_fn: Callable, params: Optional[Dict] = None,
                   force: bool = False):
    """Legacy-compatible feature computation.
    
    Old usage: feature_data = my_compute_func(window=7)
    New usage: feature_data = legacy_feature('entropy_7d', my_compute_func, {'window': 7})
    
    Under the hood: FeatureStore.get_or_compute() + auto-register.
    """
    # Auto-register if not exists
    try:
        _registry.register(name=name, hypothesis="Migrated from legacy pipeline",
                          pathway="statistical", status="draft")
    except ValueError:
        pass  # already registered
    
    return _store.get_or_compute(name, compute_fn, params, force)


def legacy_bulk_features(feature_configs: List[Dict]) -> Dict[str, Any]:
    """Compute multiple features in batch.
    
    feature_configs: [{'name': 'entropy_7d', 'fn': ..., 'params': {...}}, ...]
    Returns: {'entropy_7d': data, 'std_7d': data, ...}
    """
    results = {}
    for cfg in feature_configs:
        results[cfg['name']] = legacy_feature(
            cfg['name'], cfg['fn'], cfg.get('params'))
    return results


# ============================================================
# ADAPTER: Evaluation
# ============================================================

def legacy_evaluate(feature_values: List[float], target_values: List[float],
                    metadata: Optional[Dict] = None) -> Dict[str, Any]:
    """Legacy-compatible evaluation.
    
    Old: audit_metric = compute_tii(feature, target)
    New: results = legacy_evaluate(feature, target)
    
    Returns all metrics: TII, independence, robustness, OUI, DIS, DVI, RSI
    """
    return _evaluator.evaluate(feature_values, target_values, metadata)


def legacy_batch_evaluate(features: Dict[str, List[float]],
                          target: List[float]) -> Dict[str, Dict]:
    """Evaluate multiple features against target in batch.
    
    Returns: {'entropy_7d': {'TII': ..., 'OUI': ...}, ...}
    """
    results = {}
    for name, values in features.items():
        results[name] = _evaluator.evaluate(values, target)
    return results


# ============================================================
# ADAPTER: Training
# ============================================================

_model_cache: Dict[str, BaseModel] = {}


def legacy_train(model_type: str, X_train, y_train,
                 params: Optional[Dict] = None,
                 name: Optional[str] = None) -> BaseModel:
    """Legacy-compatible model training.
    
    Old: model = LogisticRegression().fit(X, y)
    New: model = legacy_train('logistic_regression', X, y)
    
    Supports: logistic_regression, lightgbm, random_forest
    """
    model_name = name or f"{model_type}_{datetime.now().strftime('%H%M%S')}"
    model = create_model(model_type, name=model_name, params=params)
    model.fit(X_train, y_train)
    _model_cache[model_name] = model
    return model


def legacy_predict(model: BaseModel, X, return_proba: bool = False):
    """Legacy-compatible prediction.
    
    Old: preds = model.predict(X)
    New: preds = legacy_predict(model, X)
    """
    if return_proba:
        return model.predict_proba(X)
    return model.predict(X)


# ============================================================
# ADAPTER: Decision
# ============================================================

_decision_engine = DecisionEngine()


def legacy_decision(model_output: float,
                    feature_context: Optional[Dict] = None,
                    alert_threshold: float = 0.5,
                    watch_threshold: float = 0.3) -> Dict[str, Any]:
    """Legacy-compatible decision.
    
    Old: alert = model_output > threshold
    New: result = legacy_decision(model_output, feature_context)
    
    Returns dict with: alert, alert_level, confidence, risk_score, recommendation
    """
    engine = DecisionEngine(alert_threshold=alert_threshold,
                           watch_threshold=watch_threshold)
    decision = engine.decide(model_output, feature_context)
    return decision.to_dict()


# ============================================================
# ADAPTER: Monitoring
# ============================================================

_monitor = MonitoringEngine()


def legacy_monitor(feature_values: Dict[str, List[float]],
                   target_values: List[float],
                   decisions: List[Dict]) -> Dict[str, Any]:
    """Legacy-compatible monitoring.
    
    Returns: TII, OUI, DIS, DVI, RSI, ODRI
    """
    # Convert decision dicts to OperationalDecision objects
    from .decision_api import OperationalDecision
    ods = []
    for d in decisions:
        od = OperationalDecision(**{k: v for k, v in d.items()
                                     if k in OperationalDecision.__dataclass_fields__})
        ods.append(od)
    return _monitor.compute_all(feature_values, target_values, ods)
