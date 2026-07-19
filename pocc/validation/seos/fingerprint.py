"""SEOS Fingerprint Chain — hash chain for pipeline integrity.

Each stage produces a SHA256. Chaining detects any tampering.
"""
import json
from .config import PROVENANCE_DIR
from .utils import now_iso, sha256_str

class FingerprintChain:
    """Builds a hash chain across pipeline stages."""

    def __init__(self):
        self.entries = []
        self._prev_hash = None

    def add(self, stage: str, content: bytes, metadata: dict = None):
        content_hash = sha256_str(content)
        chain_input = f"{self._prev_hash or 'GENESIS'}:{stage}:{content_hash}"
        chain_hash = sha256_str(chain_input)

        entry = {
            "stage": stage,
            "content_hash": content_hash,
            "chain_hash": chain_hash,
            "prev_chain_hash": self._prev_hash,
            "timestamp": now_iso(),
            "metadata": metadata or {},
        }
        self.entries.append(entry)
        self._prev_hash = chain_hash
        return chain_hash

    def verify(self) -> dict:
        """Verify entire chain integrity."""
        prev = None
        broken = []
        for i, e in enumerate(self.entries):
            if e["prev_chain_hash"] != prev:
                broken.append({"index": i, "stage": e["stage"], "expected_prev": prev, "got": e["prev_chain_hash"]})
            prev = e["chain_hash"]
        return {"valid": len(broken) == 0, "entries": len(self.entries), "broken": broken}

    def to_dict(self):
        return {
            "chain_length": len(self.entries),
            "root_hash": self.entries[0]["chain_hash"] if self.entries else None,
            "tail_hash": self.entries[-1]["chain_hash"] if self.entries else None,
            "valid": self.verify()["valid"],
            "entries": self.entries,
        }

    def save(self):
        path = PROVENANCE_DIR / "fingerprint_chain.json"
        path.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")

def build_from_stages(stage_data: dict) -> FingerprintChain:
    """Build fingerprint chain from pipeline stage data."""
    chain = FingerprintChain()
    for stage, data in stage_data.items():
        content = json.dumps(data, sort_keys=True).encode()
        chain.add(stage, content, metadata={"score": data.get("score", 0)})
    chain.save()
    return chain
