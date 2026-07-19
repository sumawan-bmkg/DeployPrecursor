# LAWS Phase 6 — Quantile Bounds Audit

**Generated:** 2026-06-29 14:34:40
**Model:** 3× HGBR (quantile) — p10, p50, p90 — with sample weighting
**Samples:** 1628 pre-earthquake

## Coverage Performance

| Metric | Observed | Ideal |
|--------|----------|-------|
| Coverage (p10-p90) | 76.4% | 80% |
| Below p10 | 23.5% | 10% |
| Above p90 | 0.1% | 10% |
| Mean interval width | 0.9724 mag | - |
| Median interval width | 1.0157 mag | - |

## Pinball Loss

| Quantile | Pinball Loss |
|----------|--------------|
| q=0.10 | 0.0585 |
| q=0.50 (median) | 0.1648 |
| q=0.90 | 0.0750 |

## Per-Tier Coverage

| Tier | N | Coverage | Mean Width |
|------|---|----------|------------|
| M<5.5 | 518 | 40.0% | 1.2152 |
| M5.5-6.0 | 616 | 89.1% | 0.9732 |
| M>6.0 | 494 | 98.6% | 0.7166 |

## Interpretation

Well-calibrated: coverage close to ideal 80%.