# Q1: Scientific Data Qualification

Generated: 2026-07-15T09:16:35.255935+00:00

## Data Quality Metrics
| Metric | Value | Threshold | Status |
|--------|-------|-----------|--------|
| Total Files | 608 | - | INFO |
| Success Rate | 27.0% | >= 99% | MONITOR |
| Failure Rate | 0.0% | < 1% | PASS |
| Data Completeness | 0.0% | >= 95% | MONITOR |
| Validation Total | 0 | - | INFO |
| Validation Pass | 0 | - | INFO |

## Queue State
| Queue | Count |
|-------|-------|
| SUCCESS | 164 |
| FAILED | 0 |
| RETRY | 443 |
| WAITING | 0 |

## Scheduler Log (last 20 lines)
```
2026-07-15 13:16:20,690 [collector] INFO === SCHEDULER STARTING ===
2026-07-15 13:16:20,691 [discovery] INFO discovery started (interval=300s)
2026-07-15 13:16:20,692 [collector] INFO Started worker: discovery (interval=300s)
2026-07-15 13:16:20,692 [download] INFO download started (interval=600s)
2026-07-15 13:16:20,693 [collector] INFO Started worker: download (interval=600s)
2026-07-15 13:16:20,694 [validation] INFO validation started (interval=60s)
2026-07-15 13:16:20,695 [collector] INFO Started worker: validation (interval=60s)
2026-07-15 13:16:20,697 [runtime] INFO runtime started (interval=60s)
2026-07-15 13:16:20,698 [collector] INFO Started worker: runtime (interval=60s)
2026-07-15 13:16:20,699 [audit] INFO audit started (interval=3600s)
2026-07-15 13:16:20,699 [collector] INFO Started worker: audit (interval=3600s)
```

## Qualification Score: 38.1%
