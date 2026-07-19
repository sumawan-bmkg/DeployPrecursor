"""
safe_statistics — Numerically stable statistical operations.
All evaluator/metric functions MUST use this module.
"""
import numpy as np
from typing import Optional, List, Any


def safe_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """Pearson correlation with safe handling of edge cases."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]
    if len(x) < 3:
        return 0.0
    if np.std(x) < 1e-15 or np.std(y) < 1e-15:
        return 0.0
    from scipy.stats import pearsonr
    c, _ = pearsonr(x, y)
    return float(c) if not np.isnan(c) else 0.0


def safe_mutual_information(x: np.ndarray, y: np.ndarray,
                             n_neighbors: int = 5) -> float:
    """Mutual information with safe handling."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    mask = ~(np.isnan(x) | np.isnan(y))
    x, y = x[mask], y[mask]
    if len(x) < 10 or np.std(x) < 1e-15:
        return 0.0
    from sklearn.feature_selection import mutual_info_regression
    try:
        mi = mutual_info_regression(x.reshape(-1, 1), y, random_state=42)[0]
        return float(mi) if not np.isnan(mi) else 0.0
    except Exception:
        return 0.0


def safe_cohens_d(x: np.ndarray, y: np.ndarray) -> float:
    """Cohen's d with zero-variance protection."""
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    x = x[~np.isnan(x)]
    y = y[~np.isnan(y)]
    if len(x) < 2 or len(y) < 2:
        return 0.0
    pooled_var = (np.var(x) + np.var(y)) / 2
    if pooled_var < 1e-15:
        return 0.0
    return float((np.mean(x) - np.mean(y)) / np.sqrt(pooled_var))


def safe_variance(x: np.ndarray) -> float:
    """Variance with NaN handling."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) < 2:
        return 0.0
    return float(np.var(x))


def safe_entropy(x: np.ndarray) -> float:
    """Shannon entropy with zero-protection."""
    x = np.asarray(x, dtype=float)
    x = x[~np.isnan(x)]
    if len(x) == 0:
        return 0.0
    # Normalize to probabilities
    x_pos = x - x.min() + 1e-15
    p = x_pos / x_pos.sum()
    p = p[p > 0]
    if len(p) == 0:
        return 0.0
    return float(-np.sum(p * np.log(p + 1e-15)))


def safe_divide(a, b, default=0.0):
    """Division with zero protection."""
    if b is None or (isinstance(b, float) and (np.isnan(b) or abs(b) < 1e-15)):
        return default
    return float(a / b)


def safe_log(x, default=0.0):
    """Logarithm with non-positive protection."""
    if x is None or (isinstance(x, (int, float)) and x <= 0):
        return default
    return float(np.log(x))


def safe_sqrt(x, default=0.0):
    """Square root with non-negative protection."""
    if x is None or (isinstance(x, (int, float)) and x < 0):
        return default
    return float(np.sqrt(x))


def validate_array(x: Any, name: str = "input") -> np.ndarray:
    """Validate and clean input array. Raises ValueError on critical failure."""
    if x is None:
        raise ValueError(f"{name}: None")
    
    if isinstance(x, (list, tuple)):
        x = np.array(x, dtype=float)
    
    if not isinstance(x, np.ndarray):
        raise ValueError(f"{name}: not array-like")
    
    if len(x) == 0:
        raise ValueError(f"{name}: empty array")
    
    # Replace Inf with NaN, then remove
    x = np.where(np.isinf(x), np.nan, x)
    
    return x
