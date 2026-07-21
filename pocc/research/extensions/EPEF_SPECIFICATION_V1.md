# EPEF Specification V1.0
## Normative Document for Earthquake Precursor Evaluation

### 1. Scope
This specification defines the normative evaluation framework for all earthquake precursor prediction experiments conducted under the EPEF (Earthquake Prediction Evaluation Framework). All experiments, publications, and operational assessments SHALL adhere to these definitions unless explicitly noted.

### 2. Terminology
| Term | Definition |
|---|---|
| **Event** | A tectonic earthquake with Mw >= M_threshold occurring within the target region |
| **Alarm** | A prediction output with probability P >= P_alert issued at time T_pred |
| **Lead Time** | Δt = T_event - T_pred (positive if prediction precedes event) |
| **Hit (TP)** | Alarm issued AND event occurs within positive window |
| **False Alarm (FP)** | Alarm issued AND no event within positive window |
| **Miss (FN)** | Event occurs AND no alarm within preceding negative window |
| **Correct Null (TN)** | No alarm AND no event within window |

### 3. Event Definition
- **Magnitude Threshold**: Mw >= 5.0
- **Depth Range**: 0-100 km (crustal earthquakes)
- **Target Region**: Indonesian archipelago (95°E - 145°E, 15°S - 10°N)
- **Catalog Source**: BMKG earthquake catalog (primary), USGS/ISC (secondary verification)

### 4. Alarm Definition
- **Probability Threshold**: P >= 0.40 (primary gate)
- **Station Count**: >= 2 stations (fusion gate)
- **Confidence Filter**: QC score >= 0.50
- **Uncertainty Gate**: σ < 0.50
- **Storm Suppression**: Kp > 4 → alarm suppressed

### 5. Positive Window (for TP/FP classification)
- **Spatial Radius**: 500 km (haversine from prediction centroid)
- **Temporal Window**: 14 days (T_pred to T_pred + 14d)
- **Multi-Event Rule**: Multiple events within same window → first event matched, remainder scored as additional hits

### 6. Negative Window (for FN classification)
- **Temporal Lookback**: 14 days (T_event - 14d to T_event)
- **Spatial Radius**: 500 km

### 7. Evaluation Rules
- **Censoring**: Events within first 14 days of evaluation period are excluded (no lookback available)
- **Edge Effect**: Alarms within last 7 days of evaluation period are excluded from TP/FP scoring (window incomplete)
- **Independence**: No prediction is matched to more than one event. First-match rule applies.
- **Baseline**: Random predictor (uniform distribution across same space-time volume) and persistence predictor (previous interval)

### 8. Reporting Rules
- All metrics SHALL report 95% confidence intervals (bootstrap, n=2000)
- Statistical significance SHALL be assessed via permutation test (n=1000)
- Molchan diagram SHALL be provided for probability threshold sweep
- Reliability diagram SHALL be provided for calibration assessment
- Per-station breakdown SHALL be reported for all detection metrics
