# LAWS Phase 2 — FAISS Magnitude Evaluation

**Generated:** 2026-06-29 13:48:54
**Method:** k-NN magnitude via FAISS IndexFlatIP (cosine similarity)
**Index:** All pre-earthquake vectors, L2-normalized, Inner Product

## FAISS Index Configuration

| Parameter | Value |
|-----------|-------|
| Index Type | IndexFlatIP (brute-force exact) |
| Metric | Cosine (via L2-norm + Inner Product) |
| Vectors | 1628 (pre-earthquake only) |
| Dimension | 128 |
| k (neighbors) | 20 |
| Total index size | ~814 KB |

## Retrieval Latency

| Metric | Value |
|--------|-------|
| Total search time (1628 queries) | 0.009s |
| Per-query latency | 0.0056 ms |
| Queries per second | 177166 |

## Magnitude Estimation Accuracy

| Metric | Value |
|--------|-------|
| MAE | 0.4201 |
| RMSE | 0.5056 |
| Mean Error (bias) | -0.0016 |
| Median Abs Error | 0.3900 |

### Per-Tier Breakdown

| Tier | N | MAE | RMSE | Mean Error |
|------|---|-----|------|------------|
| M<5.5 | 518 | 0.5067 | 0.5688 | -0.5063 |
| M5.5-6.0 | 616 | 0.2003 | 0.2631 | -0.0622 |
| M>6.0 | 494 | 0.6034 | 0.6456 | 0.6034 |

### k Sensitivity Analysis

| k | MAE | RMSE | Latency (ms) |
|---|-----|------|--------------|
| 5 | 0.4392 | 0.5373 | 0.0037 |
| 10 | 0.4239 | 0.5124 | 0.0045 |
| 15 | 0.4218 | 0.5091 | 0.0056 |
| 20 | 0.4201 | 0.5056 | 0.0041 |
| 30 | 0.4198 | 0.5031 | 0.0064 |
| 50 | 0.4200 | 0.5031 | 0.0057 |

## Interpretation
MAE 0.3-0.5 — **Moderate** magnitude estimation. Usable for operational alerting with confidence bounds.