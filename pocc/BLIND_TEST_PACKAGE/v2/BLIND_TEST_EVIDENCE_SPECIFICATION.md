# Blind Test Evidence Specification

**Version:** 2.0
**Date:** 2026-07-16

---

## Purpose

Define the complete chain of evidence for every prediction, from sensor to publication.

---

## 1. Evidence Chain

```
Sensor (LEMI-30i2)
    ↓ UTC timestamp
Collector (validation worker)
    ↓ file hash
Preprocessing (CWT scalogram)
    ↓ tensor hash
Inference Engine (model + prior)
    ↓ prediction hash
Prediction Registry (append-only CSV)
    ↓ prediction UUID
Ground Truth Matching (merge2026.csv)
    ↓ match hash
Evaluation (metrics)
    ↓ evaluation hash
Evidence Package (UUID + SHA256)
    ↓ digital signature
Publication (paper-gji branch)
```

## 2. Prediction Record Schema

Every prediction in the registry must contain:

| Field | Type | Description |
|-------|------|-------------|
| prediction_uuid | uuid | Unique identifier |
| timestamp_utc | ISO 8601 | UTC time of prediction |
| station | string | 3-letter BMKG code |
| prediction_class | enum | normal/unknown/precursor/earthquake/storm |
| confidence | float [0,1] | Model confidence |
| magnitude_pred | float | Predicted magnitude (if applicable) |
| azimuth_pred | float | Predicted azimuth (degrees) |
| input_hash | hex(64) | SHA256 of input waveform file |
| output_hash | hex(64) | SHA256 of prediction output |
| checkpoint_hash | hex(64) | SHA256 of model checkpoint used |
| config_hash | hex(64) | SHA256 of deployment config |
| waveform_hash | hex(64) | SHA256 of processed scalogram tensor |
| ground_truth_hash | hex(64) | SHA256 of matching catalog entry |
| evaluation_hash | hex(64) | SHA256 of evaluation report at time of matching |
| digital_signature | hex | Optional: cryptographic signature |

## 3. Input Provenance

| Level | Hash Required | Description |
|-------|--------------|-------------|
| Raw waveform | SHA256 of `.lem` file | Source data from BMKG |
| Processed tensor | SHA256 of `.npy` scalogram | After CWT preprocessing |
| Model checkpoint | SHA256 of `.pt` file | Frozen prior model |
| Configuration | SHA256 of `deploy.py` + `main.py` | Deployment version |

## 4. Output Provenance

| Level | Hash Required | Description |
|-------|--------------|-------------|
| Prediction CSV | SHA256 of prediction row | Individual prediction |
| Matched results | SHA256 of matched CSV | After ground truth matching |
| Evaluation report | SHA256 of metrics file | After statistical analysis |
| Final evidence package | SHA256 of all above | Composite hash |

## 5. Timestamp Requirements

- All timestamps in **UTC** (ISO 8601 format: `YYYY-MM-DDTHH:MM:SSZ`)
- Prediction timestamp: when the inference was run (not when the data was recorded)
- Ground truth timestamp: event onset time from BMKG catalog
- Lead time: `ground_truth_timestamp - prediction_timestamp`
- No local time allowed in any evidence record

## 6. Evidence Package Structure

For each blind test run:

```
evidence/
├── prediction_registry.csv          (all predictions)
├── matched_results.csv              (predictions matched to events)
├── unmatched_predictions.csv        (predictions with no event match)
├── excluded_events.csv              (events excluded per policy)
├── evaluation_metrics.json          (all computed metrics)
├── bootstrap_ci.json                (confidence intervals)
├── null_model_comparison.json       (model vs null results)
├── sensitivity_analysis.json        (threshold/window/magnitude sweep)
├── physics_consistency.json         (H/Z, polarization, EEJ checks)
├── explainability/                  (per-prediction attributions)
│   ├── station_attribution.json
│   ├── frequency_attribution.json
│   ├── channel_attribution.json
│   └── temporal_attribution.json
├── reproducibility/
│   ├── requirements_frozen.txt
│   ├── random_seeds.json
│   ├── checkpoint_hashes.json
│   └── deterministic_verification.json
├── SHA256_MANIFEST.json             (hashes of all files in this package)
└── EVALUATION_REPORT.md             (human-readable summary)
```

## 7. Integrity Verification

1. All evidence files are SHA256-hashed
2. SHA256_MANIFEST.json contains hashes of all files in the package
3. Manifest itself is SHA256-hashed
4. Manifest hash is included in the paper's data availability statement
5. Evidence package is stored on server AND in a separate backup location
