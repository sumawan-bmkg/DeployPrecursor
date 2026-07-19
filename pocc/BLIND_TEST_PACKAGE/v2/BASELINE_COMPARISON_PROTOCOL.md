# Baseline Comparison Protocol

**Version:** 2.0
**Date:** 2026-07-16

---

## Purpose

Demonstrate that the proposed model provides meaningful improvement over simpler methods. Without baseline comparison, the scientific contribution is unverifiable.

---

## Required Baselines

### B1. Random Classifier

**Description:** Predict earthquake/no-earthquake randomly with probability equal to class prevalence.

**Implementation:** For each prediction window, generate random label with P(event) = prevalence (~0.076).

**Metrics:** Same as model (F1, precision, recall, AUC)

**Expected:** F1 ≈ 0.14 (for prevalence ~0.076)

---

### B2. Persistence Model

**Description:** Yesterday's prediction = today's prediction. If a prediction was made yesterday, extend it to today.

**Implementation:** Take the last prediction and propagate forward by N days.

**Expected:** F1 depends on temporal autocorrelation of events.

---

### B3. Threshold-Based (H-component variance)

**Description:** Flag an anomaly when the H-component variance exceeds 3× the 30-day rolling median.

**Implementation:** Compute rolling 30-day median of H-component variance. Flag when variance > 3× median.

**Metrics:** Same as model

**Rationale:** This is the simplest physically motivated anomaly detector. If the model cannot beat this, it is not adding value.

---

### B4. Isolation Forest

**Description:** Unsupervised anomaly detection on handcrafted features (H/D/Z variance, spectral power in Pc3/Pc4 bands, H/Z ratio).

**Implementation:** Isolation Forest on feature vector per prediction window.

**Rationale:** Strong unsupervised baseline that doesn't require labels. If the model is better, it proves the learned representation adds value over handcrafted features.

---

### B5. One-Class SVM

**Description:** One-class SVM on the same handcrafted features as Isolation Forest.

**Implementation:** One-class SVM with RBF kernel, nu=0.1, trained on quiet-day data.

**Rationale:** Another strong unsupervised baseline.

---

### B6. CNN without Graph (1D-CNN)

**Description:** CNN operating on single-station time series without cross-station graph information.

**Implementation:** Same architecture as the proposed model but without the GNN component (no message passing between stations).

**Rationale:** Ablation: proves the graph component adds value.

---

### B7. CNN + Graph (Proposed model)

**Description:** The full PIMES model as deployed.

**Rationale:** This is the system being evaluated.

---

### B8. Physics-Only Rule

**Description:** Simple rule-based system: alarm if (H/Z ratio changes > 50%) AND (spectral power in 0.01-1 Hz increases > 2σ) AND (Kp < 4) AND (Dst > -30 nT).

**Implementation:** Rule-based detector using standard ULF precursor criteria from literature.

**Rationale:** Tests whether the model learns physics or just statistics.

---

## Comparison Protocol

| Metric | B1 | B2 | B3 | B4 | B5 | B6 | B7 | B8 |
|--------|----|----|----|----|----|----|----|----|
| F1 | | | | | | | | |
| AUC-ROC | | | | | | | | |
| AUC-PR | | | | | | | | |
| Recall | | | | | | | | |
| Precision | | | | | | | | |
| MCC | | | | | | | | |
| Brier | | | | | | | | |
| ECE | | | | | | | | |
| Lead time (mean) | | | | | | | | |
| FAR (per day) | | | | | | | | |

**Statistical comparison:** McNemar's test (model vs each baseline), paired bootstrap test.

**Minimum claim:** Model B7 must have significantly higher F1 than B1-B6 with p < 0.05.

---

## Ablation Analysis

| Variant | Graph | Channel info | Frequency info | Cosmic info |
|---------|-------|-------------|----------------|-------------|
| B6 (CNN-1D) | No | No | No | No |
| B7-GNN only | Yes | No | No | No |
| B7-CNN+cosmic | No | Yes | Yes | Yes |
| B7-full (proposed) | Yes | Yes | Yes | Yes |

Each ablation variant shows the marginal contribution of each component.
