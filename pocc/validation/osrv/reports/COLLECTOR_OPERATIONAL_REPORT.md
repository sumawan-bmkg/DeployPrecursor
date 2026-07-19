# Collector Operational Validation Report

Generated: 2026-07-15T09:10:16.119756+00:00

## Queue State
| Queue | Count |
|-------|-------|
| SUCCESS | 164 |
| FAILED | 0 |
| RETRY | 443 |
| WAITING | 0 |
| TOTAL | 608 |

## Reliability
| Metric | Value |
|--------|-------|
| Success Rate | 27.0% |
| Failure Rate | 0.0% |
| Retry Rate | 72.9% |
| Queue Size | 0 |

## Scheduler Log (Last 20 lines)
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

## Recommendations
- System healthy
- Queue draining
