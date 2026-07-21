# Explainability Framework — LAWS V2

## 1. Motivation
BMKG operators require interpretable predictions:
- *Why* did this station show high probability?
- *Which* precursor method (QG/PC3/CWT) contributed most?
- *Is* this a genuine precursor or space weather artifact?

## 2. Station Contribution Analysis
For each fused prediction, decompose by station:

\[
\text{Contribution}_s = \frac{w_s \cdot P_s}{\sum_{i} w_i \cdot P_i}
\]

Output: Bar chart of station contributions for each event.

## 3. Precursor Method Attribution
Decompose each station prediction by precursor method:

\[
P_s = \alpha_{\text{QG}} \cdot P_{\text{QG},s} + \alpha_{\text{PC3}} \cdot P_{\text{PC3},s} + \alpha_{\text{CWT}} \cdot P_{\text{CWT},s}
\]

Output: Stacked bar showing QG/PC3/CWT proportions.

## 4. Temporal Importance
Given input window (7 days), which day contributed most to prediction?

GradCAM-like approach:

\[
w_t = \frac{\partial P}{\partial x_t} \cdot x_t
\]

Heatmap: Prediction sensitivity over input time series.

## 5. Feature Attribution via SHAP
For model outputs, compute SHAP values:

```python
import shap
explainer = shap.Explainer(model, X_background)
shap_values = explainer(X_instance)
shap.plots.waterfall(shap_values[0])
```

Output: Waterfall plot showing each feature's contribution to P.

## 6. Confidence Map
Visualise prediction confidence geographically:

```text
Map of Indonesia overlay:
  Station locations colored by P_s
  Voronoi cells colored by prediction probability
  Fused event centroids with confidence buffer
```

## 7. Output Specification
For each prediction, the system SHALL log:
- Per-station probability breakdown
- Per-method contribution (QG/PC3/CWT)
- Storm gate status (Kp value)
- Top-3 contributing stations
- Attention-weighted input segment (for CWT)
