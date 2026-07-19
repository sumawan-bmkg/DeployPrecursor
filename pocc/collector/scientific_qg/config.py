"""QCConfig - Rule configuration with YAML/JSON support."""
from .discovery import DEFAULT_RULES


class QCConfig:
    """YAML-compatible QC configuration."""
    def __init__(self, rules=None):
        if rules is None:
            rules = {r_cls.name: True for r_cls in DEFAULT_RULES}
        self.rule_configs = rules

    def is_enabled(self, rule_name):
        return self.rule_configs.get(rule_name, True)

    @classmethod
    def from_yaml_dict(cls, d):
        return cls(rules=d.get("rules", {}))

    @classmethod
    def all_disabled(cls):
        return cls(rules={r_cls.name: False for r_cls in DEFAULT_RULES})
