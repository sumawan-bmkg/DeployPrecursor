"""SEOS Provenance — artifact lineage tracking.

Every artifact gets a global UUID + parent UUID forming a directed acyclic graph.
"""
import json
from .config import PROVENANCE_DIR, PIPELINE_STAGES
from .utils import now_iso, new_uuid, sha256_str, log_append

class Artifact:
    def __init__(self, name, stage, parent=None, **kwargs):
        self.uuid = new_uuid()
        self.name = name
        self.stage = stage
        self.parent_uuid = parent.uuid if parent else None
        self.timestamp = now_iso()
        self.metadata = kwargs
        self._hash = sha256_str(json.dumps({"name": name, "stage": stage,
                                             "ts": self.timestamp, **kwargs}))

    def to_dict(self):
        return {
            "uuid": self.uuid, "name": self.name, "stage": self.stage,
            "parent_uuid": self.parent_uuid, "timestamp": self.timestamp,
            "content_hash": self._hash, "metadata": self.metadata,
        }

def build_lineage(collector_data: dict, pipeline_stages: dict, prediction_data: dict) -> list:
    """Build full provenance chain from collector to prediction."""
    artifacts = []

    # Root: collector data
    root = Artifact("collector_data", "collector",
                    station=collector_data.get("station", "unknown"),
                    total_files=collector_data.get("total_files", 0))
    artifacts.append(root)

    # Pipeline stages
    parent = root
    for stage_name in PIPELINE_STAGES:
        stage_data = pipeline_stages.get(stage_name, {})
        art = Artifact(stage_name, "pipeline",
                       parent=parent,
                       status=stage_data.get("status", "UNKNOWN"),
                       score=stage_data.get("score", 0))
        artifacts.append(art)
        parent = art

    # Prediction
    pred = Artifact("prediction", "output",
                    parent=parent,
                    station=prediction_data.get("station", "unknown"),
                    magnitude=prediction_data.get("magnitude", 0),
                    confidence=prediction_data.get("confidence", 0))
    artifacts.append(pred)

    return artifacts

def save_lineage(artifacts: list):
    """Save provenance chain to disk (append-only)."""
    chain = [a.to_dict() for a in artifacts]
    chain_id = chain[0]["uuid"][:8] if chain else "empty"

    # Save full chain
    path = PROVENANCE_DIR / f"lineage_{chain_id}.json"
    path.write_text(json.dumps(chain, indent=2), encoding="utf-8")

    # Append to master index
    index = PROVENANCE_DIR / "lineage_index.jsonl"
    log_append(index, {
        "ts": now_iso(), "chain_id": chain_id,
        "artifacts": len(chain),
        "root_uuid": chain[0]["uuid"] if chain else None,
        "last_uuid": chain[-1]["uuid"] if chain else None,
    })

    return chain_id
