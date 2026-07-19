# Data Qualification Gate Checklist

**Purpose:** Before `blindtest-start` tag, verify BMKG waveform data meets minimum quality.
**Location:** `/opt/pimes/incoming/`

---

## Pre-Qualification Checks

| # | Check | Method | Pass/Fail | Notes |
|---|-------|--------|-----------|-------|
| 1 | SHA256 checksum matches manifest | `sha256sum --check sha256.txt` | ❓ | |
| 2 | File count matches manifest | `wc -l sha256.txt` vs file count | ❓ | |
| 3 | Station count | Count unique station codes | ❓ | Expect 21+ |
| 4 | Time coverage | `2025-12-01` to `2026-06-30` | ❓ | |
| 5 | UTC verification | All timestamps in UTC (not WIB) | ❓ | Critical |
| 6 | Sampling rate | All files at 64 Hz (±1%) | ❓ | LEMI-30i2 spec |
| 7 | Missing segments | Check for gaps > 60 min | ❓ | |
| 8 | Metadata | Station code, lat, lon, elevation, sensor type | ❓ | Per file header |
| 9 | Sensor consistency | Same sensor type across files | ❓ | |
| 10 | Noise screening | SNR > 3 dB in 0.01-10 Hz band | ❓ | |

---

## Post-Qualification Actions

| Action | Condition | Trigger |
|--------|-----------|---------|
| Move to production | All checks pass | `mv incoming/*.lem production/` |
| Update prediction registry | After production import | `python deploy.py doctor` |
| Tag blindtest-start | After verification | `git tag blindtest-start` |
| Start blind test | After tag | Per BLIND_TEST_RUNBOOK.md |

## If Checks Fail

| Failure | Action |
|---------|--------|
| Checksum mismatch | Request re-send from BMKG |
| UTC not confirmed | Run timezone conversion, document in evaluation report |
| Sampling rate deviation | Flag station as degraded, exclude if > 5% deviation |
| Missing station | Document which stations are missing, evaluate on available ones |
| High noise | Exclude affected station-hours, document exclusion |
