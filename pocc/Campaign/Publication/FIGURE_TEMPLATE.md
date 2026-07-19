# Figure Template for Paper

**Target journal:** Geophysical Journal International (GJI)
**Figures to prepare:**

---

## Figure 1: System Architecture

**Type:** Block diagram
**Content:** PIMES operational platform components (collector → preprocessing → tensor → inference → prediction → dashboard → OSC → CEPSL)
**Reference:** `PIMES_SCIENTIFIC_DATA_BOOK/KNOWLEDGE_GRAPH.md`
**Status:** [ ] Draft [ ] Final

---

## Figure 2: Data Pipeline

**Type:** Flowchart
**Content:** Station → .lem file → CWT scalogram → tensor → Bayesian inference → prediction
**Reference:** SBTP v2.0 Section 2
**Status:** [ ] Draft [ ] Final

---

## Figure 3: Dashboard Screenshot

**Type:** UI screenshot
**Content:** PIMES Operational Dashboard (overview page or mission page)
**Reference:** `http://10.20.229.43:8500/mission`
**Status:** [ ] Draft [ ] Final

---

## Figure 4: Station Map

**Type:** Geographic map
**Content:** All BMKG stations with priors (21 stations), color-coded by EEJ zone. Megathrust zones marked.
**Reference:** EEJ classification report
**Status:** [ ] Draft [ ] Final

---

## Figure 5: ROC Curve

**Type:** Line plot
**Content:** ROC curve for proposed model + diagonal (random). AUC annotation. 95% CI band.
**Axes:** x=FPR (0-1), y=TPR (0-1)
**Status:** [ ] Draft [ ] Final

---

## Figure 6: PR Curve

**Type:** Line plot
**Content:** PR curve for proposed model. Horizontal line = random baseline (prevalence).
**Axes:** x=Recall (0-1), y=Precision (0-1)
**Status:** [ ] Draft [ ] Final

---

## Figure 7: Reliability Diagram

**Type:** Line plot
**Content:** Calibration curve. Diagonal = perfect calibration. Bin mean confidence vs bin accuracy. ECE annotation.
**Axes:** x=Mean confidence (0-1), y=Accuracy (0-1)
**Status:** [ ] Draft [ ] Final

---

## Figure 8: Confusion Matrix

**Type:** Heatmap (2×2)
**Content:** TP, FP, FN, TN with counts. Normalized by class.
**Status:** [ ] Draft [ ] Final

---

## Figure 9: Lead Time Distribution

**Type:** Histogram + boxplot
**Content:** Distribution of lead times for all true positive predictions. Mean + median annotated.
**Axes:** x=Lead time (hours), y=Count
**Status:** [ ] Draft [ ] Final

---

## Figure 10: Station Attribution

**Type:** Heatmap
**Content:** Per-station F1 scores (21 stations), color-coded by performance tier (A/B/C/D). EEJ zone overlay.
**Reference:** Evaluation protocol per-station metrics
**Status:** [ ] Draft [ ] Final

---

## Figure 11: Physics Validation

**Type:** Panel plot (2×2 or 3×1)
**Content:**
- (a) H/Z ratio during TP vs quiet periods
- (b) Polarization ratio during TP vs quiet periods
- (c) Dst correlation scatter plot
- (d) Day/night FAR bar chart
**Status:** [ ] Draft [ ] Final

---

## Figure 12: FP Characterization

**Type:** Stacked bar chart
**Content:** FP counts stratified by Dst range (quiet/mod/storm) and time of day (day/night)
**Axes:** x=Dst range, y=FP count, fill=time of day
**Status:** [ ] Draft [ ] Final

---

## Figure 13: Blind Test Timeline

**Type:** Gantt-style timeline
**Content:** Campaign day → prediction count → events. Horizontal timeline showing prediction density.
**Status:** [ ] Draft [ ] Final

---

## Figure 14: Null Model Comparison

**Type:** Bar chart
**Content:** F1 scores for all 8 model variants. Error bars = 95% bootstrap CI. Star = proposed model.
**Status:** [ ] Draft [ ] Final

---

## Table 1: Primary Results

**Type:** Table
**Content:** All model variants with metrics (see BASELINE_RESULT_TEMPLATE.md)

---

## Table 2: Per-Station Results

**Type:** Table
**Content:** 21 stations with precision, recall, F1, FAR

---

## Table 3: Stratified Results

**Type:** Table
**Content:** By Dst, time-of-day, EEJ zone, magnitude

---

## Table 4: Sensitivity Analysis

**Type:** Table
**Content:** F1 range across threshold, window, magnitude, spatial tolerance

---

## Supplementary Figure S1: Dropout Stability Test

**Type:** Line plot showing prediction stability across repeated runs

---

## Supplementary Figure S2: Example Anomaly

**Type:** Time series of waveform + scalogram + prediction for one TP event

---

## Supplementary Figure S3: EEJ Map

**Type:** Color-coded station map with EEJ zones

---

## Summary

| Figure | Type | Priority | Needs BT Results? |
|--------|------|----------|-------------------|
| 1. Architecture | Diagram | High | No |
| 2. Data pipeline | Diagram | High | No |
| 3. Dashboard | Screenshot | High | No |
| 4. Station map | Map | High | No |
| 5. ROC | Plot | High | Yes |
| 6. PR | Plot | High | Yes |
| 7. Calibration | Plot | High | Yes |
| 8. Confusion matrix | Heatmap | High | Yes |
| 9. Lead time | Histogram | High | Yes |
| 10. Station attribution | Heatmap | High | Yes |
| 11. Physics validation | Panel | Medium | Yes |
| 12. FP characterization | Bar | Medium | Yes |
| 13. Timeline | Gantt | Medium | Yes |
| 14. Null comparison | Bar | High | Yes |
| S1. Stability | Line | Low | Yes |
| S2. Example anomaly | Series | Medium | Yes |
| S3. EEJ map | Map | Low | No |
