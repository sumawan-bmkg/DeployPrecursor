"""
magbind.core — Operational Kernel for BMKG Earthquake Early Warning.
All operational logic should be accessed through this package.
"""
from .registry import FeatureRegistry, FeatureRecord
from .evaluator import UnifiedEvaluator
from .feature_store import FeatureStore
from .model_api import BaseModel, create_model, MODEL_REGISTRY
from .decision_api import DecisionEngine, OperationalDecision
from .monitoring import MonitoringEngine

from .compat import legacy_feature, legacy_bulk_features, legacy_evaluate, legacy_batch_evaluate, legacy_train, legacy_predict, legacy_decision, legacy_monitor
__version__ = "1.0.0"
