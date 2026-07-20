#!/usr/bin/env python3
"""
laws_predictor.py — Real LAWS V9.5 PredictorInterface implementation.

Calls LAWS predict_cli.py via subprocess. Falls back to MockPredictor on failure.
"""
import json, subprocess, logging, time
from collector.predictor_base import PredictorInterface, Prediction
from collector.mock_predictor import MockPredictor

log = logging.getLogger("laws_predictor")

LAWS_VENV = "/opt/pimes/laws/runtime/.venv/bin/python"
LAWS_CLI = "/opt/pimes/laws/predict_cli.py"


class LAWSRealPredictor(PredictorInterface):
    """Loads V9.5 checkpoint and runs real inference via subprocess."""

    def __init__(self, device="cpu", fallback=None):
        self.device = device
        self.fallback = fallback or MockPredictor(mode="deterministic")
        self._version = "laws-v9.5-champion"
        self._loaded = False
        self._load_test()

    def _load_test(self):
        """Quick test to verify model can load."""
        try:
            r = subprocess.run(
                [LAWS_VENV, LAWS_CLI, "--help"],
                capture_output=True, text=True, timeout=10
            )
            if r.returncode == 0:
                self._loaded = True
                log.info("LAWS V9.5 model CLI available")
            else:
                log.warning("LAWS CLI error: %s", r.stderr[:200])
        except Exception as e:
            log.warning("LAWS model not available: %s", str(e)[:100])

    def get_name(self) -> str:
        return "LAWSV95Real"

    def get_model_info(self) -> dict:
        return {
            "model_name": self.get_name(),
            "version": self._version,
            "device": self.device,
            "cli": LAWS_CLI,
            "status": "loaded" if self._loaded else "unavailable",
            "fallback": self.fallback.get_name(),
        }

    def predict(self, context) -> Prediction:
        if not self._loaded:
            return self.fallback.predict(context)

        station = getattr(context, 'station', 'unknown') if context else 'unknown'
        h5_date = getattr(context, 'h5_date', None) if context else None
        h5_dir = getattr(context, 'h5_dir', '/opt/pimes/2026/scalogram') if context else '/opt/pimes/2026/scalogram'

        t0 = time.time()
        try:
            cmd = [LAWS_VENV, LAWS_CLI, "--station", station, "--device", self.device]
            if h5_date:
                cmd.extend(["--h5-date", h5_date])
            if h5_dir:
                cmd.extend(["--h5-dir", h5_dir])

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if result.returncode != 0:
                log.warning("LAWS inference failed: %s", result.stderr[:200])
                return self.fallback.predict(context)

            data = json.loads(result.stdout.strip())
            if "error" in data:
                log.warning("LAWS error: %s", data["error"][:200])
                return self.fallback.predict(context)

            latency = data.get("latency_ms", (time.time() - t0) * 1000)

            # Convert detection_prob to probability format
            det_prob = data.get("detection_prob", 0.0)
            uncertainty = abs(0.5 - det_prob) * 2  # distance from decision boundary
            confidence = 1.0 - uncertainty

            return Prediction(
                probability=round(det_prob, 4),
                confidence=round(confidence, 4),
                uncertainty=round(uncertainty, 4),
                azimuth=data.get("azimuth_deg"),
                station=station,
                explanation=f"V9.5 P={det_prob:.4f} gate={data.get('gate_value',0):.4f}",
                model_version=self._version,
                model_name=self.get_name(),
                backend="laws-v9.5-real",
                latency_ms=round(latency, 1),
                timestamp=time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()),
                qc_version="sciqg-1.0",
                pipeline_version="laws-v2",
            )
        except subprocess.TimeoutExpired:
            log.warning("LAWS inference timeout for %s", station)
            return self.fallback.predict(context)
        except Exception as e:
            log.error("LAWS predictor error: %s", str(e)[:200])
            return self.fallback.predict(context)
