"""Plugin discovery - auto-find all QCRule subclasses."""
import importlib, inspect, os, pkgutil
from .rules.base import QCRule

_RULES_CACHE = None


def discover_rules():
    """Auto-discover all QCRule subclasses from rules/ directory."""
    global _RULES_CACHE
    if _RULES_CACHE is not None:
        return _RULES_CACHE
    rules = []
    pkg_dir = os.path.dirname(__file__)
    rules_dir = os.path.join(pkg_dir, "rules")
    if os.path.isdir(rules_dir):
        for importer, modname, ispkg in pkgutil.iter_modules([rules_dir]):
            if modname == "base" or modname.startswith("_"):
                continue
            try:
                mod = importlib.import_module(f".rules.{modname}", package=__package__)
                for name, obj in inspect.getmembers(mod):
                    if (inspect.isclass(obj) and issubclass(obj, QCRule)
                            and obj is not QCRule and obj.name != "base_rule"):
                        if obj not in rules:
                            rules.append(obj)
            except Exception:
                pass
    # Sort by priority if available
    priority_order = {"CRITICAL": 0, "HIGH": 1, "NORMAL": 2, "MEDIUM": 3, "LOW": 4}
    rules.sort(key=lambda r: (priority_order.get(getattr(r, 'priority', 'NORMAL'), 99), getattr(r, 'name', '')))
    _RULES_CACHE = rules
    return rules


DEFAULT_RULES = discover_rules()
