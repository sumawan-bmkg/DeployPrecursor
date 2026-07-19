# Explainability Protocol

**Version:** 2.0
**Date:** 2026-07-16

---

## Purpose

For every prediction, provide evidence that the model is making decisions based on physically meaningful features, not spurious correlations.

---

## 1. Station Attribution

**Question:** Which stations contributed most to this prediction?

**Method:** GNN attention weights (if available) or GNNExplainer.

**Output per prediction:**
- Top-3 contributing stations (ranked by attribution score)
- Geographic proximity to epicenter (for TP predictions)
- If top contributor is > 500 km from epicenter, flag for review

---

## 2. Frequency Attribution

**Question:** Which frequency bands drove this prediction?

**Method:** Integrated Gradients on scalogram input channels.

**Output per prediction:**
- Dominant frequency band (0.001-0.01, 0.01-0.1, 0.1-1, 1-10, 10-32 Hz)
- Spectral power change relative to quiet-day baseline
- If dominant frequency is > 10 Hz, flag as possible noise

---

## 3. Channel Attribution

**Question:** Which magnetic component (H, D, Z) contributed most?

**Method:** Integrated Gradients on channel dimension.

**Output per prediction:**
- H contribution (%), D contribution (%), Z contribution (%)
- If Z contribution < 20%, flag for physics review (Z should be significant for deep sources)

---

## 4. Temporal Attribution

**Question:** Which time period preceding the event was most informative?

**Method:** Integrated Gradients on time dimension of scalogram.

**Output per prediction:**
- Hours before event with highest attribution
- If highest attribution is > 48h before event, this is consistent with long-term preparation
- If highest attribution is < 1h before event, this may be co-seismic artifact

---

## 5. Attention Map

**Method:** If the GNN uses attention, report attention matrix for each prediction.

**Output:** Heatmap of station-to-station attention weights.

---

## 6. Physics Explanation

For each TP prediction, generate a natural-language explanation:

```
Prediction for [STATION] at [TIME]:
- Confidence: [XX]%
- Contributing stations: [A, B, C]
- Dominant frequency: [XX Hz]
- Dominant channel: [H/D/Z]
- Time of highest attribution: [XX hours before event]
- Physics consistency: [CHECK/FLAG]
- Flag: [NONE/EEJ/STORM/UNKNOWN]
```

---

## 7. Uncertainty Quantification

For each prediction:
- If using Bayesian inference: report posterior mean and 95% credible interval
- If using ensemble: report mean and standard deviation across ensemble members
- If single model: report prediction confidence as proxy for uncertainty

---

## 8. False Positive Characterization

After blind test, cluster all FPs by:
- Station distribution (which stations produce most FPs?)
- Time-of-day distribution (mostly daytime = possible EEJ)
- Dst range (mostly storm = possible magnetospheric contamination)
- Frequency distribution (dominant frequency of FP predictions)
- Duration (short-lived vs persistent FPs)

---

## 9. Per-Station Performance Report

For each of the 21 prediction-capable stations, report:
- TP count, FP count, FN count
- Precision, recall, F1
- Dominant contributing frequency
- Day/night FAR ratio
- Distance to nearest epicenter (for TP)

---

## 10. Minimum Viable Explainability Package

Before GJI submission, the paper must include:
1. Figure: Station attribution heatmap (top events)
2. Figure: Frequency attribution bar chart (averaged over all TPs)
3. Figure: Channel contribution pie chart (averaged over all TPs)
4. Figure: Temporal attribution time series (aligned to event onset)
5. Table: Per-station performance metrics
6. Table: FP characterization by Dst range and time-of-day
