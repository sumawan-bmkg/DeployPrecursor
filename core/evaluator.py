"""UnifiedEvaluator — single evaluator for all operational metrics."""
import numpy as np
from typing import List, Optional, Dict, Any


class UnifiedEvaluator:
    """Single evaluator: computes TII, OUI, DIS, DVI, RSI in one call."""
    
    @staticmethod
    def evaluate(feature_values: List[float], target_values: List[float],
                 metadata: Optional[Dict] = None) -> Dict[str, Any]:
        from scipy.stats import pearsonr
        from sklearn.feature_selection import mutual_info_regression
        
        fv = np.array(feature_values, dtype=float)
        tv = np.array(target_values, dtype=float)
        
        mask = ~(np.isnan(fv) | np.isnan(tv))
        fv = fv[mask]; tv = tv[mask]
        
        if len(fv) < 10:
            return {"error": "Insufficient samples", "n_samples": len(fv)}
        
        results = {"n_samples": len(fv), "warnings": []}
        
        # TII
        mi = mutual_info_regression(fv.reshape(-1, 1), tv, random_state=42)[0]
        tii = min(100, mi * 200)
        if fv.std() > 0 and tv.std() > 0:
            upper = fv[tv > np.percentile(tv, 75)]
            lower = fv[tv < np.percentile(tv, 25)]
            if len(upper) > 1 and len(lower) > 1:
                d = (np.mean(upper) - np.mean(lower)) / np.sqrt(
                    (np.std(upper)**2 + np.std(lower)**2) / 2)
                tii = min(100, max(tii, abs(d) * 30))
        results["TII"] = round(tii, 2)
        
        # Independence
        lag1 = pearsonr(fv[:-1], fv[1:])[0] if len(fv) > 3 else 0
        results["independence"] = round(max(0, 1 - abs(lag1)), 3)
        
        # Robustness
        n_boot = min(100, len(fv) - 1)
        if n_boot > 10:
            corrs = []
            rng = np.random.RandomState(42)
            for _ in range(n_boot):
                idx = rng.choice(len(fv), len(fv), replace=True)
                c, _ = pearsonr(fv[idx], tv[idx])
                if not np.isnan(c): corrs.append(c)
            r = max(0, min(1, (1 - np.std(corrs)) * 3)) if corrs else 0.5
        else:
            r = 0.5
        results["robustness"] = round(r, 3)
        
        # OUI
        results["OUI"] = round(min(100, tii * 0.5 + results["independence"] * 30 + r * 20), 2)
        
        # DIS
        results["DIS_contribution"] = round(
            min(1.0, tii / 100 * 0.6 + results["independence"] * 0.2 + r * 0.2), 3)
        
        # DVI
        dvi = r * 0.5 + results["independence"] * 0.3
        dvi += (1 - abs(np.mean(fv) / max(abs(np.mean(fv)), 1))) * 0.2
        results["DVI_contribution"] = round(min(1.0, dvi), 3)
        
        # RSI
        if len(fv) > 10:
            noise = np.random.RandomState(42).normal(0, fv.std() * 0.05, len(fv))
            mi_noisy = mutual_info_regression(
                (fv + noise).reshape(-1, 1), tv, random_state=42)[0]
            rsi = max(0, 1 - abs(mi - mi_noisy) / max(mi, 0.01))
        else:
            rsi = 0.5
        results["RSI_sensitivity"] = round(rsi, 3)
        
        return results
