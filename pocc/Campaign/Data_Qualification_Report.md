# Data Qualification Report

**Purpose:** Gate C entry pass. Must be signed before `blindtest-start`.
**To be filled when BMKG waveform 2025-2026 arrives at `incoming/`.**

---

## Metadata

| Field | Value |
|-------|-------|
| Waveform source | BMKG operational ULF stations |
| Expected period | 2025-12 to 2026-06 |
| Expected stations | ≥ 21 (matching prior_*.pt files) |
| Format | `.lem` (LEMI-30i2) or `.mlb` (specified) |
| Sample rate | 64 Hz nominal |
| Data arrival date | ❓ |
| Checksum manifest | ❓ (provide SHA256 file) |
| Contact | ❓ (BMKG data custodian) |

---

## Pre-Qualification Results

| # | Check | Method | Result | Evidence |
|---|-------|--------|--------|----------|
| 1 | SHA256 checksum match | `sha256sum --check manifest.txt` | ❓ | `evidence/checksum_result.txt` |
| 2 | File count | `ls *.lem \| wc -l` | ❓ | `evidence/file_count.txt` |
| 3 | Station count | Unique station codes | ❓ | `evidence/station_list.txt` |
| 4 | Time coverage | Min/max timestamps | ❓ | `evidence/time_range.txt` |
| 5 | UTC synchronization | Timezone in header | ❓ | `evidence/utc_check.txt` |
| 6 | Sampling rate verification | `64 ± 1% Hz` | ❓ | `evidence/sample_rate.txt` |
| 7 | Missing segments | Gaps > 60 min | ❓ | `evidence/gap_report.txt` |
| 8 | Metadata completeness | Headers readable | ❓ | `evidence/metadata_check.txt` |
| 9 | Sensor consistency | Consistent model across files | ❓ | `evidence/sensor_check.txt` |
| 10 | Noise screening | SNR > 3 dB in 0.01-10 Hz | ❓ | `evidence/noise_profile.txt` |

---

## Qualification Decision

| Result | Action |
|--------|--------|
| ✅ ALL PASS | → Move to production/ → `git tag blindtest-start` |
| ⚠️ MINOR FAIL (checks 7-10) | → Flag in report, proceed with exclusions documented |
| ❌ CRITICAL FAIL (checks 1-6) | → HOLD. Request corrected data from BMKG. |

---

## Signatures

| Role | Name | Date | Signature |
|------|------|------|-----------|
| Data Custodian (BMKG) | | | |
| Technical Lead (PIMES) | | | |
| ERB Chair | | | |

---

## Post-Approval

Once signed:

```bash
mv /opt/pimes/incoming/*.lem /opt/pimes/data/raw/<STATION>/
git tag blindtest-start
# Execute per BLIND_TEST_RUNBOOK.md
```
