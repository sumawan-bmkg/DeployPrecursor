# Statistical Validation Protocol

**Version:** 2.0
**Date:** 2026-07-16

---

## 1. ROC Curve

**Purpose:** Threshold-independent evaluation of discrimination ability.

**Procedure:**
1. Sweep classification threshold from 0 to 1 in 0.01 steps
2. At each threshold, compute TPR (recall) and FPR = 1 - specificity
3. Plot ROC curve: TPR vs FPR
4. Compute AUC via trapezoidal integration
5. Report 95% bootstrap CI for AUC

**Interpretation:**
- AUC = 0.5: random classifier (no skill)
- AUC = 0.7: acceptable
- AUC = 0.8: good
- AUC = 0.9: excellent

**Limitation:** For imbalanced data, ROC can be misleadingly optimistic. Must be reported alongside PR curve.

---

## 2. PR Curve

**Purpose:** More informative than ROC for imbalanced/rare-event data.

**Procedure:**
1. At each confidence threshold, compute precision and recall
2. Plot precision vs recall
3. Compute AUC-PR (average precision)
4. Compute baseline AUC-PR = prevalence (fraction of positive events)
5. Report improvement over baseline

**Interpretation:**
- AUC-PR = prevalence: no skill
- AUC-PR > 2× prevalence: moderate skill
- AUC-PR > 4× prevalence: good skill

---

## 3. Calibration Assessment

**Purpose:** Verify that confidence scores reflect true probabilities.

**Procedure:**
1. Bin predictions into 10 equal-width bins by confidence
2. In each bin, compute mean confidence and observed accuracy
3. Plot reliability diagram: mean confidence (x) vs accuracy (y)
4. Diagonal = perfect calibration
5. Compute ECE and MCE

**ECE formula:**
ECE = (1/N) Σ |B_m| × |acc(B_m) - conf(B_m)|

where B_m is the m-th bin, |B_m| is the number of predictions in that bin.

**MCE formula:**
MCE = max_m |acc(B_m) - conf(B_m)|

---

## 4. Bootstrap Confidence Intervals

**Purpose:** Quantify uncertainty in all point estimates.

**Procedure:**
1. Resample the matched prediction-catalog pairs (with replacement)
2. Compute metric (F1, precision, recall, etc.) on resampled data
3. Repeat 5,000 times
4. Take 2.5th and 97.5th percentiles as 95% CI
5. Report CI alongside point estimate for every metric

**Rationale:** Parametric CI assumes normality, which is violated for imbalanced binary outcomes. Bootstrap is non-parametric.

---

## 5. Permutation Test

**Purpose:** Test whether model skill is statistically significant vs. random chance.

**Procedure:**
1. Compute true F1 (or other metric) on original data
2. Shuffle event-catalog pairings randomly (shuffle which predictions are matched to which events)
3. Compute F1 on shuffled data
4. Repeat 1,000 times
5. p-value = (rank of true F1) / 1,000
6. Report p-value

**Interpretation:**
- p < 0.01: strong evidence against null hypothesis (model has skill)
- p < 0.05: moderate evidence
- p ≥ 0.05: insufficient evidence (model may not have skill)

---

## 6. McNemar's Test

**Purpose:** Compare two models (e.g., model vs null) on the same dataset.

**Procedure:**
1. Build 2×2 contingency table of correct/incorrect predictions for both models
2. Compute McNemar's χ² statistic
3. Report p-value

**When to use:** When comparing model vs. null model at the same operating threshold.

---

## 7. Wilcoxon Signed-Rank Test

**Purpose:** Compare two sets of paired confidence scores.

**Procedure:**
1. For each prediction, compute the difference in confidence between model and null
2. Rank the absolute differences
3. Compute Wilcoxon W statistic
4. Report p-value

**When to use:** To test whether model confidence scores are systematically higher than null model for true positives.

---

## 8. Effect Size (Cohen's d)

**Purpose:** Quantify the magnitude of difference between two conditions.

**Formula:** d = (M₁ - M₂) / S_pooled

**Interpretation:**
- d < 0.2: negligible
- 0.2 < d < 0.5: small
- 0.5 < d < 0.8: medium
- d > 0.8: large

---

## 9. Power Analysis

**Purpose:** Determine if the sample size (number of events) is sufficient to detect a meaningful effect.

**Procedure:**
1. Set α = 0.05 (Type I error)
2. Set β = 0.20 (Type II error, power = 0.80)
3. Compute minimum detectable effect size for current sample
4. Report whether current N (events) is sufficient

**For 1,356 events at prevalence 7.6/day:**
- ~1,356 events in 177 days → sufficient for most analyses
- For per-station analysis (~65 events/station): may be underpowered

---

## 10. Null Model Comparison

Define and compare against 3 null models:

| Null Model | Description | Expected F1 |
|------------|-------------|-------------|
| Random | Predict with same rate as prevalence | ~0.076 × 2 / (1 + 0.076) ≈ 0.14 |
| Persistence | Yesterday's prediction = today's | Depends on autocorrelation |
| Threshold | H-component variance > 3σ | To be computed |

**Minimum requirement:** Model F1 must exceed all null model F1 with p < 0.05.

---

## 11. Sensitivity Analysis

Sweep key parameters and report metric surfaces:

| Parameter | Range | Steps |
|-----------|-------|-------|
| Confidence threshold | 0.1 - 0.9 | 0.1 |
| Tolerance window ΔT | 6h, 12h, 24h, 48h | 4 |
| Magnitude cutoff | 3.5, 4.0, 4.5, 5.0 | 4 |
| Spatial tolerance D | 100, 300, 500, 1000 km | 4 |

Report: F1 surface plots, threshold-dependent F1, stability assessment.
