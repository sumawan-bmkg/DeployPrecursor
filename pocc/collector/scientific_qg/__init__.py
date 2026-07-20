"""LAWS V2 ScientificQG - Pure functional quality gate."""
from .engine import ScientificQG
from .result import QCResult, RuleResult, score_to_severity, score_action
from .config import QCConfig
from .context import RuleContext
from .discovery import discover_rules, DEFAULT_RULES
from .rules import (
    QCRule, RangeRule, ContinuityRule, MissingSampleRule,
    SpectralRule, EntropyRule, CrossCorrelationRule, PSDRule,
    FlatlineRule,
)
