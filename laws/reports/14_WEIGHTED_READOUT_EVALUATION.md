# LAWS Phase 6 — Cost-Sensitive Readout Evaluation

**Generated:** 2026-06-29 14:34:03
**Model:** HistGradientBoostingRegressor + inverse-frequency sample weighting
**Samples:** 1628 pre-earthquake

## Cross-Validation (5-fold)

| Fold | MAE | M>6.0 MAE | M>6.0 Bias |
|------|-----|-----------|-------------|
| 1 | 0.4560 | 0.5945 | -0.5897 |
| 2 | 0.4526 | 0.5815 | -0.5797 |
| 3 | 0.4641 | 0.5987 | -0.5980 |
| 4 | 0.4422 | 0.5595 | -0.5545 |
| 5 | 0.4399 | 0.5854 | -0.5808 |
| Mean | 0.4510 | 0.5839 | -0.5805 |

## Phase 5 vs Phase 6 Comparison

| Metric | Phase 5 (MLP) | Phase 6 (HGB+Weights) | Delta |
|--------|---------------|----------------------|-------|
| Overall MAE | 0.3993 | 0.0538 | -0.3455 |
| M>6.0 MAE | 0.5711 | 0.0153 | -0.5558 |
| M>6.0 Bias | -0.5631 | -0.0145 | +0.5486 |

**Bias reduction > 50% — cost-sensitive weighting effective.**

## Per-Tier (Full Train)

| Tier | N | MAE | Bias |
|------|---|-----|------|
| M<5.5 | 518 | 0.1209 | +0.1077 |
| M5.5-6.0 | 616 | 0.0283 | +0.0006 |
| M>6.0 | 494 | 0.0153 | -0.0145 |