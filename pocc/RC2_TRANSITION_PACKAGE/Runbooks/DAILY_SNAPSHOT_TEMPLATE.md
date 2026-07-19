# Daily Scientific Snapshot Template

**Version:** v2.0.0-rc2-freeze

## Format (auto-generated each day)

```
========================================
PIMES DAILY SCIENTIFIC SNAPSHOT
Date: YYYY-MM-DD
Campaign Day: N
========================================

COLLECTOR
  Uptime:        XXh XXm
  Files today:   N
  Total files:   N
  Status:        RUNNING / STOPPED

OSC
  Snapshots:     N total, N today
  Baseline:      LOCKED / COMPROMISED
  Last snapshot: HH:MM UTC

CEPSL
  Archive hash:  VERIFIED / MISMATCH
  Snapshots:     N

EVIDENCE
  Total items:   N
  New today:     N
  Chain:         INTACT

PREDICTIONS
  Total:         N
  Today:         N
  Confidence avg: X.XX

ANOMALIES
  Total:         N
  Today:         N
  Pending:       N

ALERTS
  Total:         N
  Critical:      N
  Warning:       N

HEALTH
  Score:         XX/100
  Drift:         NONE / LOW / HIGH
  Components:    XX/XX OK

SYSTEM
  Disk used:     XX GB / 492 GB (XX%)
  Load average:  X.XX
  UTC:           YYYY-MM-DDHH:MM:SSZ

STATUS: Platform operational. Awaiting waveform data.
========================================
```

## How to Generate

```bash
# Run after each campaign day
python deploy.py status > daily_snapshot_$(date +%Y%m%d).txt
```
