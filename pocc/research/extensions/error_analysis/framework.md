# Error Analysis Framework — EPEF V1.0

## 1. Spatial Error Analysis
Analysis of errors as function of geographic location.

### Metrics
| Item | Method | Output |
|---|---|---|
| Error heatmap | 2D kernel density of FP vs FN | Spatial bias map |
| Distance error | $\Delta d = ||\text{prediction\_loc} - \text{event\_loc}||$ | CDF curve |
| Region breakdown | 5km x 5km grid cells | Per-cell metric |

### Expected Insight
"Model over-predicts in Java region (dense stations), under-predicts in Papua (sparse stations)."

## 2. Temporal Error Analysis
Errors as function of time.

### Metrics
| Item | Method | Output |
|---|---|---|
| Error rate over time | Rolling 30-day window | Trend plot |
| Seasonal breakdown | Monthly aggregation | Seasonal pattern |
| Diurnal analysis | Hour-of-day aggregation | Diurnal bias |

### Expected Insight
"False alarm rate increases during monsoon season (Nov-Mar)."

## 3. Station Error Analysis
Per-station and inter-station error patterns.

### Metrics
| Item | Method | Output |
|---|---|---|
| Per-station FN/FP | Individual station scoring | Station ranking |
| Inter-station correlation | FP co-occurrence matrix | Redundancy map |
| Distance-to-station | $d_{\min}$ for each event | Coverage gap |

## 4. Magnitude Error Analysis
Error as function of earthquake magnitude.

### Metrics
| Item | Method | Output |
|---|---|---|
| Recall by magnitude bin | Mw 5.0-5.5, 5.5-6.0, etc. | Magnitude sensitivity |
| FAR by magnitude bin | Same bins | Magnitude false alarm rate |

## 5. Lead Time Error Analysis
Error as function of lead time.

### Metrics
| Item | Method | Output |
|---|---|---|
| Lead time bias distribution | Histogram of Δt | Bias plot |
| Lead time vs confidence | Scatter plot | Confidence-lead relationship |

## 6. Seasonal Error Analysis
Error patterns by month, solar cycle, and geomagnetic activity.

### Metrics
| Item | Method | Output |
|---|---|---|
| Monthly FAR | Per-month aggregation | Seasonal pattern |
| Kp bin analysis | FAR per Kp bin | Storm-induced FP |
| Solar cycle phase | Active vs quiet sun | Cycle dependence |
