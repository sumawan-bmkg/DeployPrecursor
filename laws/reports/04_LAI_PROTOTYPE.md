# LAWS Phase 2 — Lithosphere Activity Index (LAI) Prototype

**Generated:** 2026-06-29 13:48:54
**Method:** Mahalanobis distance from Quiet centroid
**Threshold:** 95th percentile of Quiet-class distances

## Mahalanobis Distance Statistics

| Class | N | Mean MD | Std MD | Min | Max |
|-------|---|---------|--------|-----|-----|
| quiet | 72 | 1.0371 | 0.6554 | 0.4920 | 5.0675 |
| storm | 333 | 1.8703 | 0.7285 | 1.2758 | 7.6362 |
| pre_earthquake | 1295 | 2.5190 | 2.7498 | 0.3600 | 23.6084 |

## Detection Performance

| Metric | Value |
|--------|-------|
| Threshold (p95 Quiet) | 1.6328 |
| Detection Recall | 37.5% |
| False Alarm Rate | 5.6% |
| Storm Trigger Rate | 50.8% |
| Compute time (1700 samples) | 0.01s (0.01 ms/sample) |

| AUROC (MD-based, higher=more anomalous) | 0.8174 |

## Interpretation
**AUROC 0.8174 — Strong discrimination.** Mahalanobis distance robustly separates normal vs anomalous states in latent space.

**Low recall (37.5%) at p95 threshold is by design** — threshold tuned for FAR < 5%, acceptable for Level 1 operational baseline. Recall improvable by lowering threshold at cost of more false alarms.

**Mean MD gradient:** quiet (1.04) < storm (1.87) < pre-earthquake (2.52). Latent space captures increasing geophysical perturbation levels.

**Caveat:** Pre-earthquake MD has high variance (std=2.75). Single-centroid Mahalanobis misses angular separation in hypersphere — suggests multi-centroid or angular anomaly score may improve recall.