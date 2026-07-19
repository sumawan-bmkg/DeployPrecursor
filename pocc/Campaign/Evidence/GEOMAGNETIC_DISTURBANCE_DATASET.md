# Geomagnetic Disturbance Dataset

**Generated:** 2026-07-16
**Data source:** cosmic_features_v3.csv (hourly Kp/Dst)
**Period:** 2025-12 to 2026-06 (matching merge2026.csv)

---

## 1. Storm Classification

| Category | Dst range | Kp range | Description |
|----------|-----------|----------|-------------|
| Quiet | Dst > -20 nT | Kp 0-2 | No geomagnetic disturbance |
| Moderate | -50 < Dst ≤ -20 nT | Kp 3-4 | Slightly disturbed |
| Storm | -100 < Dst ≤ -50 nT | Kp 5-6 | Moderate geomagnetic storm |
| Severe Storm | Dst ≤ -100 nT | Kp 7-9 | Severe geomagnetic storm |

---

## 2. Disturbance Periods (from cosmic_features_v3.csv)

To be filled after querying the CSV:

| Date | Hour (UTC) | Dst | Kp | Category | Notes |
|------|-------------|-----|-----|----------|-------|
| | | | | | |

---

## 3. Prediction Context

For every prediction in the blind test registry, the following context will be recorded:

| Context Field | Source | Resolution |
|--------------|--------|------------|
| Dst at prediction time | cosmic_features_v3.csv | Hourly |
| Kp at prediction time | cosmic_features_v3.csv | Hourly |
| Storm category | Dst-based | Per hour |
| Solar activity (if AE available) | cosmic_features_v3.csv | Hourly |
| Local time at station | Station long + UTC | Computed |
| Season | Calendar date | Daily |

---

## 4. Usage in Evaluation

### 4.1 Dst-Stratified FAR
Report FAR separately for each storm category. If FAR increases significantly during storms, the model is detecting magnetospheric signals.

### 4.2 Dst-Stratified Accuracy
Report recall and precision separately for each Dst bin. If the model performs better during storms, it may be using storm-related features.

### 4.3 Prediction Count by Dst Range
| Dst Range | Predictions | TPs | FPs | FAR | Recall |
|-----------|-------------|-----|-----|-----|--------|
| Dst > -20 | | | | | |
| -50 to -20 | | | | | |
| -100 to -50 | | | | | |
| Dst < -100 | | | | | |

---

## 5. Solar F10.7 cm Flux (if available)

The solar radio flux F10.7 is a proxy for solar EUV radiation, which influences ionospheric density and EEJ strength. If available, stratify predictions by F10.7 quartile.

---

## 6. Implementation

This dataset is populated automatically from `cosmic_features_v3.csv` when running the blind test evaluation. The file paths:

```
/opt/pimes/data/cosmic_features_v3.csv
/pocc/Campaign/Evaluation/geomagnetic_context.csv
```
