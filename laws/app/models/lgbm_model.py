#!/usr/bin/env python3
"""
lgbm_model.py — LightGBM magnitude regression inference module.

Loads pre-trained LightGBM Huber regressor (.pkl) and provides
predict_magnitude(features) for operational LAWS deployment.

Expected features: 53 ULF2 tabular features (list or numpy array).
"""
import logging
from pathlib import Path
from typing import List, Union, Optional

import numpy as np
import joblib

logger = logging.getLogger(__name__)


class LgbmMagInference:
    """
    LightGBM magnitude regressor wrapper for LAWS.

    Usage:
        model = LgbmMagInference(checkpoint_path)
        mag = model.predict(features_53_element_list)
    """

    def __init__(
        self,
        checkpoint_path: Path,
        expected_n_features: int = 53,
    ):
        self.expected_n_features = expected_n_features
        self.checkpoint_path = Path(checkpoint_path)

        if not self.checkpoint_path.exists():
            raise FileNotFoundError(
                f'LightGBM checkpoint not found: {self.checkpoint_path}'
            )

        self.model = joblib.load(str(self.checkpoint_path))
        logger.info('LightGBM model loaded from %s', self.checkpoint_path)

    def predict(
        self,
        features: Union[List[float], np.ndarray],
    ) -> float:
        """
        Predict magnitude from 53 ULF2 features.

        Args:
            features: List or 1D array of 53 float features.

        Returns:
            float: Estimated magnitude (Mw).
        """
        # Convert to numpy
        if isinstance(features, list):
            x = np.array(features, dtype=np.float32)
        elif isinstance(features, np.ndarray):
            x = features.astype(np.float32)
        else:
            raise TypeError(
                f'Expected list or np.ndarray, got {type(features).__name__}'
            )

        # Validate dimensions
        if x.ndim == 1:
            x = x.reshape(1, -1)

        n_feats = x.shape[1]
        if n_feats != self.expected_n_features:
            raise ValueError(
                f'Expected {self.expected_n_features} features, '
                f'got {n_feats}. '
                f'Feature count mismatch in input array.'
            )

        mag = self.model.predict(x)
        return float(mag[0])


# ─── Standalone helper ────────────────────────────────────────────
def predict_magnitude(
    features: Union[List[float], np.ndarray],
    checkpoint_path: Optional[Path] = None,
    model: Optional[LgbmMagInference] = None,
) -> float:
    """
    Convenience function for LightGBM magnitude prediction.

    Provide either a pre-loaded `model` instance or a `checkpoint_path`.
    """
    if model is not None:
        return model.predict(features)
    if checkpoint_path is not None:
        inst = LgbmMagInference(checkpoint_path)
        return inst.predict(features)
    raise ValueError('Either `model` or `checkpoint_path` must be provided.')
