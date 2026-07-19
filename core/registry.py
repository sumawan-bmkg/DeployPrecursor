"""FeatureRegistry — central governance for all operational features."""
import csv, uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List


@dataclass
class FeatureRecord:
    """Single feature with full governance metadata."""
    feature_id: str = ""
    name: str = ""
    hypothesis: str = ""
    pathway: str = ""
    owner: str = ""
    version: str = "1.0"
    status: str = "draft"
    lineage: str = ""
    lifetime: str = ""
    operational_score: float = 0.0
    created_at: str = ""
    updated_at: str = ""
    source_code: str = ""
    description: str = ""
    
    def __post_init__(self):
        if not self.feature_id:
            self.feature_id = str(uuid.uuid4())
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        self.updated_at = datetime.now().isoformat()


class FeatureRegistry:
    """Central registry for all operational features."""
    
    def __init__(self, path: Optional[Path] = None):
        self.records: Dict[str, FeatureRecord] = {}
        self.path = path or Path("core_feature_registry.csv")
        self._load()
    
    def register(self, name, hypothesis="", pathway="statistical",
                 owner="system", version="1.0", status="draft",
                 description="") -> FeatureRecord:
        if name in self.records:
            raise ValueError(f"Feature '{name}' already registered")
        r = FeatureRecord(name=name, hypothesis=hypothesis, pathway=pathway,
                         owner=owner, version=version, status=status,
                         description=description)
        self.records[name] = r
        self._save()
        return r
    
    def get(self, name) -> Optional[FeatureRecord]:
        return self.records.get(name)
    
    def update(self, name, **kwargs) -> Optional[FeatureRecord]:
        r = self.records.get(name)
        if not r: return None
        for k, v in kwargs.items():
            if hasattr(r, k): setattr(r, k, v)
        r.updated_at = datetime.now().isoformat()
        self._save()
        return r
    
    def list_by_status(self, status):
        return [r for r in self.records.values() if r.status == status]
    
    def list_by_pathway(self, pathway):
        return [r for r in self.records.values() if r.pathway == pathway]
    
    def all(self):
        return list(self.records.values())
    
    def _load(self):
        if not self.path or not self.path.exists(): return
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                for row in csv.DictReader(f):
                    self.records[row["name"]] = FeatureRecord(**row)
        except: pass
    
    def _save(self):
        if not self.path: return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        records = self.all()
        if not records: return
        fnames = list(asdict(records[0]).keys())
        with open(self.path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fnames)
            w.writeheader()
            for r in records: w.writerow(asdict(r))
