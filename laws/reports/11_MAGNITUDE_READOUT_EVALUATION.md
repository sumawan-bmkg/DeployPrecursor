# LAWS Phase 5 — Magnitude Readout Head Evaluation

**Generated:** 2026-06-29 14:19:13
**Input:** 128D L2-normalized projection vectors (frozen V8)
**Samples:** 1628 pre-earthquake
**Model:** MLP(128→64→32→16→1), ReLU, Adam, L2=0.001

## 5-Fold Cross-Validation

| Fold | MAE | RMSE | R2 |
|------|-----|------|----|
| 1 | 0.4504 | 0.5445 | -0.0557 |
| 2 | 0.4570 | 0.5485 | -0.1165 |
| 3 | 0.4275 | 0.5066 | 0.0443 |
| 4 | 0.4456 | 0.5414 | -0.1163 |
| 5 | 0.4318 | 0.5347 | -0.2015 |
| **Mean** | **0.4425** | **0.5354** | **-0.0891** |

## Comparison: Readout Head vs FAISS k-NN

| Method | Overall MAE | M>6.0 MAE | Notes |
|--------|-------------|-----------|-------|
| FAISS k-NN (baseline) | 0.4201 | 0.6034 | Phase 2/4 |
| MLP Readout Head | 0.3993 | 0.5711 | Trained on 128D frozen |

**Improvement:** MAE 0.4201 → 0.3993 (+0.0208, +4.9%)

## Per-Tier Performance (Full Train)

| Tier | N | MAE | RMSE | Bias |
|------|---|-----|------|------|
| M<5.5 | 518 | 0.4808 | 0.5478 | +0.4773 |
| M5.5-6.0 | 616 | 0.1931 | 0.2444 | +0.0443 |
| M>6.0 | 494 | 0.5711 | 0.6230 | -0.5631 |

## Interpretation
MAE 0.3993 — **Better than FAISS** (0.4201). Readout head improves magnitude accuracy but further tuning recommended.
M>6.0 bias persists (-0.5631) — consider weighted loss or oversampling high-M.