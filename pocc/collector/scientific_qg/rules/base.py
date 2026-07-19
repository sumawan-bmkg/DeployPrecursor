"""Base class for all QC rules. Plugin architecture."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..context import RuleContext


class QCRule(ABC):
    """Base class. Plugin architecture. Auto-discovered."""
    name: str = "base_rule"
    version: str = "1.0"
    category: str = "general"
    description: str = ""
    weight: float = 1.0
    priority: str = "NORMAL"  # CRITICAL, HIGH, NORMAL, LOW
    enabled: bool = True

    def __init_subclass__(cls, **kw):
        super().__init_subclass__(**kw)
        if cls.name == "base_rule":
            cls.name = cls.__name__.replace("Rule", "").lower()

    @abstractmethod
    def evaluate(self, ctx: RuleContext) -> dict:
        """Return dict with 'passed', 'metric', 'value' keys."""

    def run(self, ctx: RuleContext) -> dict:
        if not self.enabled:
            return {"passed": True, "metric": None, "value": None}
        return self.evaluate(ctx)
