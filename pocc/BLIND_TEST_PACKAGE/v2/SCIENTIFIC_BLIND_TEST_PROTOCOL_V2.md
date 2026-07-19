# SBTP v2.0 — Blind Test Evaluation Protocol

**Version:** 2.0
**Date:** 2026-07-16
**Baseline:** v2.0.0-rc2-freeze
**Constraint:** Protocol only — no code, no model changes

---

## 1. Dataset Policy

### 1.1 Inclusion Criteria

| Criterion | Threshold | Notes |
|-----------|-----------|-------|
| Waveform quality | SNR > 3 dB above baseline | Measured as signal power / noise power in 0.01-10 Hz band |
| Temporal coverage | ≥ 80% completeness per 24-hour window | 20% gap is acceptable via interpolation |
| Station status | Online and validated by collector | Collector validation worker must pass |
| Sampling rate | 64 Hz (±1%) | LEMI-30i2 nominal |
| Channels | H, D, Z present and valid | Missing channel → exclude station for that period |
| Time format | UTC-converted from file header | If WIB (UTC+7), converted before processing |

### 1.2 Exclusion Criteria

| Criterion | Action |
|-----------|--------|
| Sensor saturation | Exclude affected time window |
| Amplitude clipping (>90% full scale) | Exclude affected time window |
| Instrument calibration drift > 5 nT/week | Exclude station for that period |
| Missing channel data > 20% | Exclude station-day combination |
| Known RFI (power line harmonics, local seismic activity) | Flag in metadata, exclude if > 10 nT amplitude |
| Station relocation | Exclude station from start date of relocation |

### 1.3 Missing Data Policy

- **Gaps < 5 minutes:** Linear interpolation in pre-processing
- **Gaps 5-60 minutes:** No interpolation; mark as unavailable for that window
- **Gaps > 60 minutes:** Exclude entire station-day combination
- **Multi-station gaps:** If < 3 stations available in a region, flag region as low-confidence

### 1.4 Corrupted Waveform Policy

- File fails SHA256 checksum → **exclude and log**
- File contains NaN or Inf values → **exclude and log**
- File header inconsistent with body → **exclude and log**

### 1.5 Duplicated Event Policy

- Same earthquake listed twice in catalog → **merge to earliest record**, log duplicate
- Same station recorded twice for same period → **use earliest valid recording**, log duplicate

### 1.6 Station Outage Policy

- Known outage (from BMKG metadata): exclude station for that period
- Unknown outage (detected by collector): exclude and flag for investigation
- Partial outage (< 24h): exclude affected hours only

---

## 2. Prediction Policy

### 2.1 Valid Prediction

A prediction is valid when:
1. The prediction has a non-null confidence score
2. The prediction timestamp is within a valid data window
3. The prediction station has valid data for that period
4. The prediction is recorded in the prediction registry before any post-processing

### 2.2 Prediction Window

- A prediction is defined as: `Prediction = (station, time, class, confidence, magnitude_pred, azimuth_pred)`
- The prediction window is the period over which the model produces outputs
- For operational use: continuous (every inference step)
- For evaluation: one prediction per station per inference window (e.g., 1-hour windows)

### 2.3 Lead Time

- Lead time = `prediction_time - event_onset_time`
- For evaluation: predictions with lead time ≤ `T_max` are considered relevant
- Recommended: `T_max = 48 hours` (accounts for 6h minimum + uncertainty)

### 2.4 Tolerance Window

- For temporal matching: `±ΔT` hours around catalog event time
- Recommended: `ΔT = 24 hours`
- Rationale: Physical mechanism is not instantaneous; precursor signals can begin hours to days before

### 2.5 Overlapping Prediction Handling

- Multiple predictions from different stations for the same event: **count each once**
- Use the highest-confidence prediction as the representative for event-level evaluation
- All predictions are still logged in the registry for station-level analysis

### 2.6 Duplicate Prediction Handling

- Same station, same time, same class → **use first occurrence** (append-only registry)
- If different station, different time: independent predictions

---

## 3. Ground Truth Policy

### 3.1 Event Matching

- An event is "detected" if at least one valid prediction exists within the tolerance window `±ΔT`
- Matching is done at station level, then aggregated to event level
- One prediction per event for event-level metrics; all predictions for station-level metrics

### 3.2 Magnitude Threshold

| Threshold | Use |
|-----------|-----|
| M ≥ 3.5 | High sensitivity (more events, more noise) |
| M ≥ 4.0 | Standard (default threshold) |
| M ≥ 4.5 | High confidence (fewer events, less noise) |
| M ≥ 5.0 | Significant events only |
| M ≥ 6.0 | Major events (small sample size) |

Default: **M ≥ 4.0** for primary evaluation, all thresholds reported for sensitivity analysis.

### 3.3 Spatial Tolerance

- Station-to-epicenter distance: `D < 500 km` (default)
- Sensitivity: also report D < 300 km and D < 1000 km

### 3.4 Event Merging

- If two catalog entries are < 1 hour apart and < 100 km apart → **merge as single event** (likely same earthquake with duplicate entry)
- Use the higher-magnitude entry as ground truth

### 3.5 Aftershock Policy

- After any M ≥ 5.0 mainshock: aftershocks (within 100 km, 72 hours) are **excluded from evaluation**
- Rationale: Post-seismic magnetic signals can contaminate the data; these are not independent precursor signals
- Document excluded aftershock count

### 3.6 Foreshock Policy

- Events < 72 hours before a larger event within 100 km are **flagged as potential foreshocks**
- Included in evaluation but reported separately
- If the model correctly predicts a foreshock, it is still counted as a true positive

### 3.7 Swarm Policy

- Seismic swarms (≥ 5 events in 24 hours within 50 km) → **merge as single event** for evaluation
- Use the largest magnitude as ground truth

---

## 4. Evaluation Metric Definitions

### 4.1 Classification Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| Precision | TP / (TP + FP) | Of all predictions, how many are correct? |
| Recall (POD) | TP / (TP + FN) | Of all events, how many were detected? |
| Specificity | TN / (TN + FP) | Of all non-events, how many were correctly rejected? |
| F1 Score | 2·P·R / (P + R) | Harmonic mean of precision and recall |
| Balanced Accuracy | (Sensitivity + Specificity) / 2 | Accuracy balanced across classes |
| MCC | (TP·TN - FP·FN) / √((TP+FP)(TP+FN)(TN+FP)(TN+FN)) | Correlation coefficient; robust to imbalance |
| Brier Score | (1/N)·Σ(p_i - o_i)² | Probabilistic accuracy of confidence scores |

### 4.2 Ranking Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| AUC-ROC | Area under ROC curve | Discrimination ability (threshold-independent) |
| AUC-PR | Area under PR curve | Precision-recall tradeoff (better for imbalanced) |
| Average Precision | Σ(n_k·R_k) / total_events | Weighted average of precision at recall thresholds |

### 4.3 Calibration Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| ECE | (1/M)·Σ|B_m|·|acc(B_m) - conf(B_m)| | Expected calibration error (lower = better) |
| MCE | max_m |acc(B_m) - conf(B_m)| | Maximum calibration error |

### 4.4 Temporal Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| Mean Lead Time | (1/TP)·Σ LT_i | Average warning time |
| Median Lead Time | Median(LT_i) | Robust central tendency of lead time |
| Lead Time CI | Bootstrap 95% CI | Uncertainty in lead time estimate |

### 4.5 Error Metrics

| Metric | Formula | Interpretation |
|--------|---------|----------------|
| Magnitude Error | |M_pred - M_true| | Mean absolute error in magnitude |
| Azimuth Error | arccos(cos(θ_pred - θ_true)) | Angular error in degrees |

---

## 5. Statistical Analysis Requirements

All metrics above must be reported with:
- **Point estimate** (primary result)
- **95% bootstrap CI** (5,000 resamples)
- **Sensitivity to threshold** (confidence threshold sweep 0.1-0.9)
- **Sensitivity to tolerance window** (ΔT = 6h, 12h, 24h, 48h)
- **Sensitivity to magnitude cutoff** (M ≥ 3.5, 4.0, 4.5, 5.0)
- **Stratification** by: time-of-day, Dst range, season, station

---

## 6. Acceptance Thresholds

| Metric | Minimum (Grade C) | Target (Grade B) | Excellent (Grade A) |
|--------|--------------------|-------------------|---------------------|
| F1 | > 0.60 | > 0.74 | > 0.85 |
| Recall | > 0.70 | > 0.80 | > 0.90 |
| Precision | > 0.60 | > 0.70 | > 0.80 |
| AUC-ROC | > 0.70 | > 0.80 | > 0.90 |
| AUC-PR | > 0.20 | > 0.40 | > 0.60 |
| ECE | < 0.15 | < 0.10 | < 0.05 |
| MCC | > 0.30 | > 0.50 | > 0.70 |
| F1 vs random null | p < 0.05 | p < 0.01 | p < 0.001 |

---

## 7. Evaluation Report Structure

The blind test evaluation report must contain:

1. Executive summary (1 page)
2. Dataset description (inclusion/exclusion, completeness)
3. Prediction summary (count, confidence distribution, station distribution)
4. Ground truth matching (matched events, unmatched events, excluded aftershocks)
5. Primary metrics (F1, precision, recall, MCC, Brier)
6. ROC and PR curves
7. Calibration diagram (reliability diagram)
8. Lead time distribution
9. Confusion matrix
10. Null model comparison (random, persistence, threshold)
11. Per-station metrics
12. Temporal stratification (day/night, season, Dst range)
13. Sensitivity analysis (threshold, window, magnitude)
14. Physics consistency check (H/Z, polarization, EEJ)
15. Explainability results (station, frequency, channel attribution)
16. Reproducibility evidence (hashes, seeds, environment)
17. Limitations and future work
