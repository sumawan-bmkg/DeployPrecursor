# LAWS Phase 3 — Time-to-Event Trajectory Audit

**Generated:** 2026-06-29 14:00:12
**Method:** Date-ordered TTE proxy (file date -> event proximity)
**Samples:** 1628 pre-earthquake

## Correlation: MD vs TTE

| Metric | Value | p-value |
|--------|-------|---------|
| Pearson r | 0.0275 | 0.2672 |
| Spearman r | 0.0294 | 0.2355 |

## MD Trend by Time-to-Event Bin

| TTE Bin | N | Mean MD | Std MD | Mean Mag |
|---------|---|---------|--------|----------|
| H-30..H-25 | 297 | 2.5358 | 2.2319 | 6.22 |
| H-25..H-20 | 266 | 2.6634 | 3.0540 | 6.25 |
| H-20..H-15 | 272 | 2.0891 | 2.0288 | 5.51 |
| H-15..H-10 | 249 | 2.4858 | 2.9375 | 5.92 |
| H-10..H-5 | 258 | 2.7037 | 3.0043 | 5.38 |
| H-5..H-1 | 226 | 1.9104 | 1.2556 | 5.40 |

## Interpretation

No significant temporal signal. V8 was not trained on temporal ordering.

## Caveat
TTE here is a date-order proxy. Real TTE requires BMKG earthquake catalog cross-reference.