# Blind Test Package — Evaluation Protocol

**Version:** v2.0.0-rc2-freeze
**Generated:** 2026-07-16

## Input Specification

| Field | Format | Source |
|-------|--------|--------|
| ULF waveform | LEMI-30i2 `.lem` or `.mlb` | BMKG operational stations |
| Station metadata | prior_*.pt (21 stations) | `laws/priors/` |
| Station signatures | station_*_signature.json (28) | `laws/runtime/validation/rdmc/` |
| Cosmic features | cosmic_features_v3.csv (Kp/Dst) | `data/` |
| Earthquake catalog | merge2026.csv (ground truth) | `initial/` |

## Output Specification

For each prediction, the system produces:
- Event UUID
- Timestamp
- Station ID
- Confidence score (0-1)
- Anomaly classification (normal / unknown / precursor / earthquake / storm)
- Magnitude prediction (if applicable)
- Azimuth prediction (if applicable)
- Lead time (hours before event)
- Runtime hash
- Model version

## Evaluation Metrics

| Metric | Definition | Target |
|--------|-----------|--------|
| **True Positive (TP)** | Predicted anomaly + event occurs within lead time | — |
| **False Positive (FP)** | Predicted anomaly + no event within lead time | Minimize |
| **False Negative (FN)** | No prediction + event occurs | Minimize |
| **True Negative (TN)** | No prediction + no event | — |
| **Precision** | TP / (TP + FP) | > 0.7 |
| **Recall** | TP / (TP + FN) | > 0.8 |
| **F1 Score** | 2 * (Precision * Recall) / (Precision + Recall) | > 0.74 |
| **Lead Time** | Hours between prediction and event | Mean > 6h |
| **Magnitude Error** | |M_pred - M_catalog| | Mean < 0.5 |
| **Azimuth Error** | Angular error (degrees) | Mean < 30° |
| **False Alarm Rate** | FP / total predictions | < 0.3 |
| **Operational Availability** | Uptime during campaign | > 0.95 |

## Lead Time Definition

A prediction is classified as TP if:
1. A catalog event (M ≥ 4.0) occurs within the prediction's lead time window
2. The station making the prediction is within the epicentral distance threshold (D < 500 km)
3. The prediction confidence exceeds the threshold (C > 0.6)

## False Alarm Definition

A prediction is classified as FP if:
1. Confidence > 0.6 and classification = "precursor" or "earthquake"
2. No catalog event occurs within the lead time window

## Acceptance Threshold

| Metric | Minimum | Description |
|--------|---------|-------------|
| Recall | 0.80 | Must detect 80% of significant events |
| Precision | 0.70 | Must have > 70% true positives |
| F1 | 0.74 | Harmonic mean of precision and recall |
| False Alarm Rate | < 0.30 | Less than 30% false alarms |
| Mean Lead Time | > 6 hours | Early warning value |
| Mean Magnitude Error | < 0.5 | Useful magnitude estimate |
| Operational Availability | > 0.95 | System must be running |

## Scoring

| Grade | F1 Score | Recall | Precision | Description |
|-------|----------|--------|-----------|-------------|
| A | > 0.85 | > 0.90 | > 0.80 | Excellent — operational deployment recommended |
| B | 0.74-0.85 | 0.80-0.90 | 0.70-0.80 | Good — operational with monitoring |
| C | 0.60-0.74 | 0.70-0.80 | 0.60-0.70 | Acceptable — requires enhancement |
| D | < 0.60 | < 0.70 | < 0.60 | Insufficient — needs research |

## Evaluation Steps (SOP)

1. Receive BMKG waveform data → place at `/opt/pimes/data/raw/`
2. Verify coverage → `python deploy.py doctor`
3. Freeze baseline → `python deploy.py deploy`
4. Collector processes waveform automatically
5. Inference engine produces predictions
6. Export predictions to CSV
7. Compare against `merge2026.csv` (ground truth)
8. Calculate metrics (precision, recall, F1, lead time, magnitude error)
9. Generate confusion matrix
10. Issue evaluation certificate

## Checklist Before Evaluation

- [ ] Waveform data present for all stations
- [ ] Catalog ground truth verified (no duplicates, no missing fields)
- [ ] All 21 prior models present
- [ ] All 28 signatures present
- [ ] CEPSL baseline locked
- [ ] OSC snapshots recording
- [ ] PDM deploy successful (health check 100%)
- [ ] Reproducibility book filled (Python version, OS, packages)
