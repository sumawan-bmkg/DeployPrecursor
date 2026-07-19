# LAWS Phase 3 — Distance-Weighted FAISS Evaluation

**Generated:** 2026-06-29 14:00:12
**Method:** Simple Mean vs Inverse Distance Weighting (IDW)

## Overall

| Method | MAE | RMSE | Mean Bias |
|--------|-----|------|-----------|
| Simple Mean | 0.4201 | 0.5056 | -0.0016 |
| Distance-Weighted | 0.4195 | 0.5064 | -0.0027 |

Delta MAE: +0.0006

## Per-Tier

| Tier | N | Simple MAE | Weighted MAE | Simple Bias | Weighted Bias |
|------|---|------------|--------------|-------------|---------------|
| M<5.5 | 518 | 0.5067 | 0.5025 | -0.5063 | -0.5022 |
| M5.5-6.0 | 616 | 0.2003 | 0.2077 | -0.0622 | -0.0634 |
| M>6.0 | 494 | 0.6034 | 0.5966 | +0.6034 | +0.5966 |

## Conclusion

M>6.0 MAE improved: 0.6034 -> 0.5966. IDW reduces regression-to-mean.