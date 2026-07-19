"""ScientificQG engine - pure validation, no side effects."""
from __future__ import annotations
import time
from .result import QCResult, RuleResult, score_to_severity
from .config import QCConfig
from .context import RuleContext
from .discovery import discover_rules


class ScientificQG:
    """Pure scientific quality gate. No filesystem, no registry, no io."""

    def __init__(self, config=None):
        self.config = config or QCConfig()
        all_rules = discover_rules()
        self.rules = [r_cls() for r_cls in all_rules if self.config.is_enabled(r_cls.name)]

    def evaluate(self, H=None, D=None, Z=None, metadata=None, station="", utc="",
                 sampling_rate=1.0, pipeline_version="", kp=None, dst=None):
        ctx = RuleContext(H=H, D=D, Z=Z, station=station, utc=utc,
                          sampling_rate=sampling_rate, pipeline_version=pipeline_version,
                          kp=kp, dst=dst, metadata=metadata or {})
        return self.evaluate_context(ctx)

    def evaluate_context(self, ctx: RuleContext) -> QCResult:
        t0 = time.perf_counter()
        failed_rules = []; warnings = []; metrics = {}
        rule_results = {}
        total_weight = 0.0; weighted_score = 0.0

        for rule in self.rules:
            r_t0 = time.perf_counter()
            result = rule.run(ctx)
            r_elapsed = (time.perf_counter() - r_t0) * 1000

            rr = RuleResult(
                name=rule.name, passed=result.get("passed", True),
                metric=result.get("metric"), value=result.get("value"),
                execution_time_ms=round(r_elapsed, 1),
                priority=getattr(rule, "priority", "NORMAL"),
                weight=getattr(rule, "weight", 1.0),
                category=getattr(rule, "category", "general"),
                version=getattr(rule, "version", "1.0"),
            )
            rule_results[rule.name] = rr

            if result.get("metric"):
                metrics[result["metric"]] = result.get("value")
            if not result["passed"]:
                failed_rules.append(rule.name)

            # Weighted score
            w = getattr(rule, "weight", 1.0)
            total_weight += w
            weighted_score += w * (1.0 if result["passed"] else 0.0)

        elapsed = (time.perf_counter() - t0) * 1000

        if not failed_rules:
            return QCResult(passed=True, score=1.0, severity="EXCELLENT",
                          metrics=metrics, execution_time_ms=round(elapsed, 1),
                          rule_results=rule_results)

        # Weighted score
        final_score = weighted_score / total_weight if total_weight > 0 else 0.0
        final_score = max(0.0, min(1.0, round(final_score, 3)))
        severity = score_to_severity(final_score)

        return QCResult(passed=final_score >= 0.40, score=final_score, severity=severity,
                       failed_rules=failed_rules, metrics=metrics,
                       execution_time_ms=round(elapsed, 1), warnings=warnings,
                       rule_results=rule_results)
