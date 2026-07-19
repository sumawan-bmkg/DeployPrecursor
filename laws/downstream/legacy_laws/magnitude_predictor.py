"""
LAWS Legacy Downstream — Magnitude Predictor
==============================================
Consumes 128D embedding from Shared Core (does NOT reload backbone).

Usage:
  from laws.downstream.legacy_laws.magnitude_predictor import MagnitudePredictor
  predictor = MagnitudePredictor()
  mag = predictor.predict(proj_128d)  # -> {"p50": 5.8, "p10": 5.3, "p90": 6.3}
"""
import os, sys, json, warnings
import numpy as np
from pathlib import Path
warnings.filterwarnings('ignore')

LAWS = Path(__file__).resolve().parents[2]
CKPT = LAWS / "checkpoints"


class MagnitudePredictor:
    """
    Lightweight magnitude readout. Consumes 128D embedding.
    Does NOT load V8 backbone — uses pre-computed embedding only.
    """

    def __init__(self):
        import joblib
        # Load quantile models (p10, p50, p90)
        self.scaler = joblib.load(str(CKPT / "quantile_scaler.joblib"))
        self.q10 = joblib.load(str(CKPT / "quantile_p10.joblib"))
        self.q50 = joblib.load(str(CKPT / "quantile_p50.joblib"))
        self.q90 = joblib.load(str(CKPT / "quantile_p90.joblib"))
        print(f"[MagnitudePredictor] Quantile models loaded from {CKPT}")

    def predict(self, proj_128d: np.ndarray) -> dict:
        """
        Predict magnitude bounds from 128D embedding.

        Args:
            proj_128d: (1, 128) L2-normalized projection vector.

        Returns:
            {"p10": float, "p50": float, "p90": float}
        """
        v_scaled = self.scaler.transform(proj_128d.astype(np.float32))
        return {
            "p10": float(self.q10.predict(v_scaled)[0]),
            "p50": float(self.q50.predict(v_scaled)[0]),
            "p90": float(self.q90.predict(v_scaled)[0]),
        }


# ── Self-test ──────────────────────────────────────────────────
if __name__ == "__main__":
    predictor = MagnitudePredictor()
    dummy = np.random.randn(1, 128).astype(np.float32)
    result = predictor.predict(dummy)
    print(f"Prediction: p50={result['p50']:.2f} "
          f"[p10={result['p10']:.2f}, p90={result['p90']:.2f}]")
    print("✅ MagnitudePredictor OK — no backbone loaded")
