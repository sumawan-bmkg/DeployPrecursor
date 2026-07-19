# Failure Injection Report

Generated: 2026-07-15T09:10:20.940338+00:00

## Scenarios
| Scenario | Severity | Recovery Strategy | RTO | Tested |
|----------|----------|-------------------|-----|--------|
| Collector down | HIGH | Auto-restart via systemd | < 60s | Not tested |
| SSH timeout | WARNING | Retry mechanism | < 300s | Built-in |
| Disk full | CRITICAL | Alert + auto-cleanup | < 600s | Not tested |
| Corrupt file | WARNING | Checksum validate + re-download | < 120s | Built-in |
| Missing station | HIGH | Alert + skip + retry | < 300s | Built-in |
| Inference fail | CRITICAL | Fallback to last prediction | < 60s | Not tested |


## Recovery Status
- Built-in mechanisms: 3/6
- Tested end-to-end: 0/6
- Recovery Time Objective: 60-600s depending on scenario

## Recommendation
Perform actual failure injection tests before Shadow Mode.
