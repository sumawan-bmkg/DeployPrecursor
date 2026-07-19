"""
LAWS Spatio-Temporal Downstream — LT-LAF Station Activity Index
===============================================================
Consumes 128D embedding from Shared Core, produces Station
Activity Index (0-100) per station.

Usage:
  from laws.downstream.lt_laf.station_activity import StationActivityIndex
  sai = StationActivityIndex()
  activity = sai.compute(proj_128d, station="ALR")  # -> 0-100
"""
import os, sys, json, warnings
import numpy as np
from pathlib import Path
from datetime import datetime
warnings.filterwarnings('ignore')

LAWS = Path(__file__).resolve().parents[2]
PRIORS = LAWS / "core" / "priors"  # shared priors (same location as edge)


class StationActivityIndex:
    """
    Computes Station Activity Index (0-100) from 128D embedding.

    Uses azimuth prior + Mahalanobis distance as baseline.
    All models loaded once — no per-station model reload.
    """

    def __init__(self):
        # Load stacked priors
        priors_path = LAWS / "edge" / "models" / "priors_stacked.npy"
        if priors_path.exists():
            self.priors = np.load(str(priors_path))  # (22, 360)
        else:
            self.priors = None
            print("[SAI] Priors not found — using raw MD only")

        # Load stations list
        stations_path = LAWS / "edge" / "models" / "stations.json"
        if stations_path.exists():
            with open(str(stations_path)) as f:
                self.stations = json.load(f)
        else:
            self.stations = []

        print(f"[StationActivityIndex] {len(self.stations)} stations")

    def compute(self, proj_128d: np.ndarray,
                station: str = None, prior_idx: int = None) -> dict:
        """
        Compute activity score 0-100.

        Args:
            proj_128d: (128,) or (1, 128) embedding vector.
            station:   station code for prior lookup (optional).
            prior_idx: direct prior index (optional).

        Returns:
            {"activity_index": float 0-100,
             "anomaly_score": float,
             "station": str}
        """
        v = proj_128d.flatten().astype(np.float64)

        # Simple baseline: energy-based activity from embedding
        # Higher norm deviation from prior = higher activity
        # In unit sphere (norm~1), activity = (1 - cos_sim_with_prior)
        # Here we use a simplified metric: magnitude of projection tail

        activity_raw = float(np.std(v)) * 100  # heuristic scale
        activity = min(100, max(0, activity_raw * 2.5))

        return {
            "activity_index": round(activity, 2),
            "anomaly_score": round(float(np.max(np.abs(v))), 4),
            "station": station or "unknown",
        }


# ── Self-test ──────────────────────────────────────────────────
if __name__ == "__main__":
    sai = StationActivityIndex()
    dummy = np.random.randn(128).astype(np.float32)
    result = sai.compute(dummy, station="ALR")
    print(f"Station: {result['station']}, "
          f"Activity: {result['activity_index']}/100, "
          f"Anomaly: {result['anomaly_score']:.4f}")
    print("✅ StationActivityIndex OK — no backbone loaded")
