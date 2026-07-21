# Blind Test Report — Template

## 1. Executive Summary
- Purpose of this blind test
- Key findings (3-5 bullet points)
- Overall verdict: GO / CONDITIONAL / NO-GO

## 2. Dataset Description
- Source: BMKG geomagnetic network
- Stations: N=23
- Period: DD/MM/YYYY — DD/MM/YYYY
- Events: N (Mw >= 5.0)
- Freeze hash: `[SHA256]`

## 3. Model Configuration
- Model: LAWSV95Real
- Version: `laws-v9.5-champion`
- Freeze hash: `[SHA256]`
- Decision thresholds: P=0.40/0.70/0.90

## 4. Detection Results

| Metric | Value | Threshold | Status |
|---|---|---|---|
| Recall | | >= 0.60 | GO/HOLD |
| Precision | | >= 0.40 | GO/HOLD |
| F1 | | >= 0.40 | GO/HOLD |
| FAR | | <= 0.60 | GO/HOLD |
| CSI | | >= 0.30 | GO/HOLD |

## 5. Forecasting Results

| Metric | Value | Threshold | Status |
|---|---|---|---|
| Brier Score | | < 0.10 | GO/HOLD |
| AUC-ROC | | > 0.70 | GO/HOLD |
| Log-Loss | | < 0.50 | GO/HOLD |

## 6. Calibration
- Reliability diagram (attached)
- Calibration slope
- Sharpness

## 7. Lead Time Analysis

| Bin | Count | Mean Lead | Min | Max |
|---|---|---|---|---|
| 1-24h | | | | |
| 1-7d | | | | |
| 7-14d | | | | |

## 8. Station Analysis
- Best performing stations (top 5)
- Worst performing stations (bottom 5)
- Coverage gaps identified

## 9. Conclusions
- Strengths
- Weaknesses
- Recommendations
- Final Verdict
