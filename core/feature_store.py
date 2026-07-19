"""FeatureStore — compute-once, cache-always."""  
import json, pickle, hashlib
from pathlib import Path
from typing import Callable, Optional, Dict


class FeatureStore:
    def __init__(self, cache_dir: Optional[Path] = None):
        from pathlib import Path as P
        self.cache_dir = cache_dir or P("cache/feature_cache")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._manifest: Dict[str, str] = {}
        self._load_manifest()
    
    def _load_manifest(self):
        mf = self.cache_dir / "manifest.json"
        if mf.exists():
            try: self._manifest = json.loads(mf.read_text())
            except: self._manifest = {}
    
    def _save_manifest(self):
        (self.cache_dir / "manifest.json").write_text(
            json.dumps(self._manifest, indent=2))
    
    def get_or_compute(self, name: str, compute_fn: Callable,
                       params: Optional[Dict] = None, force: bool = False):
        param_hash = hashlib.md5(str(params or {}).encode()).hexdigest()[:8]
        cache_key = f"{name}_{param_hash}"
        cache_path = self.cache_dir / f"{cache_key}.pkl"
        
        if not force and cache_path.exists():
            try: return pickle.loads(cache_path.read_bytes())
            except: pass
        
        data = compute_fn(**(params or {}))
        cache_path.write_bytes(pickle.dumps(data))
        self._manifest[name] = cache_key
        self._save_manifest()
        return data
    
    def clear(self, name=None):
        import shutil
        if name:
            k = self._manifest.get(name)
            if k:
                p = self.cache_dir / f"{k}.pkl"
                if p.exists(): p.unlink()
                del self._manifest[name]
        else:
            shutil.rmtree(self.cache_dir)
            self.cache_dir.mkdir(parents=True)
            self._manifest = {}
        self._save_manifest()
    
    def stats(self) -> dict:
        size = sum(f.stat().st_size for f in self.cache_dir.glob("*.pkl")) / 1e6
        return {"cached_features": len(self._manifest), "cache_size_mb": round(size, 1)}
