# Baseline Result Template — Blind Test Publication Table

**Instructions:** Fill after blind test. One row per model variant. Highlight the proposed model row.

---

## Primary Results

| Model | Precision | Recall | F1 | MCC | AUC-ROC | AUC-PR | Brier | ECE | FAR (/day) | Lead Time (mean±sd) |
|-------|-----------|--------|----|-----|---------|--------|-------|-----|------------|---------------------|
| Random | — | — | — | — | — | — | — | — | — | — |
| Persistence | — | — | — | — | — | — | — | — | — | — |
| Threshold (H-var) | — | — | — | — | — | — | — | — | — | — |
| Isolation Forest | — | — | — | — | — | — | — | — | — | — |
| One-Class SVM | — | — | — | — | — | — | — | — | — | — |
| CNN-1D | — | — | — | — | — | — | — | — | — | — |
| **CNN+GNN (Proposed)** | **—** | **—** | **—** | **—** | **—** | **—** | **—** | **—** | **—** | **—** |
| Physics Rule | — | — | — | — | — | — | — | — | — | — |

**Bootstrap 95% CI for primary metrics:** (report separately)

---

## Ablation Results

| Variant | Precision | Recall | F1 | AUC-ROC | AUC-PR |
|---------|-----------|--------|----|---------|--------|
| Full (CNN+GNN+cosmic) | — | — | — | — | — |
| -cosmic | — | — | — | — | — |
| -GNN | — | — | — | — | — |
| -graph | — | — | — | — | — |
| -CNN (GNN only) | — | — | — | — | — |

---

## Per-Station Results

| Station | Precision | Recall | F1 | FAR | FP/day | # Events | Mag Error | Az Error |
|---------|-----------|--------|----|-----|--------|----------|-----------|----------|
| ALR | — | — | — | — | — | — | — | — |
| AMB | — | — | — | — | — | — | — | — |
| ... (21) | — | — | — | — | — | — | — | — |

---

## Stratified Results

| Stratum | Precision | Recall | F1 | FAR |
|---------|-----------|--------|----|-----|
| **By Dst** | | | | |
| Dst > -20 | — | — | — | — |
| -50 < Dst ≤ -20 | — | — | — | — |
| Dst ≤ -50 | — | — | — | — |
| **By time of day** | | | | |
| Night (18-06 LT) | — | — | — | — |
| Day (06-18 LT) | — | — | — | — |
| **By EEJ zone** | | | | |
| EEJ core | — | — | — | — |
| EEJ transition | — | — | — | — |
| non-EEJ | — | — | — | — |
| **By magnitude** | | | | |
| M 3.5-4.5 | — | — | — | — |
| M 4.5-6.0 | — | — | — | — |
| M ≥ 6.0 | — | — | — | — |

---

## Sensitivity Analysis Summary

| Parameter | Range | F1 range | Stability |
|-----------|-------|----------|-----------|
| Confidence threshold | 0.1-0.9 | — to — | — |
| Tolerance window ΔT | 6h-48h | — to — | — |
| Magnitude cutoff | 3.5-5.0 | — to — | — |
| Spatial tolerance D | 100-1000 km | — to — | — |
