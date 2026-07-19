# LAWS Phase 2 — Linear Probe Audit

**Generated:** 2026-06-29 13:48:53
**Input:** 128D projection vectors from V8 SupCon (frozen)
**Dataset:** val split (1700 samples)

---
## Task A: Binary Detection (Quiet vs Pre-earthquake)

| Metric | Mean (5-fold) | Std |
|--------|---------------|-----|
| AUROC | 0.7270 | 0.0680 |
| Balanced Accuracy | 0.6220 | 0.0332 |
| Weighted F1 | 0.4257 | 0.0290 |

**Interpretation:** 
AUROC 0.7-0.9 — **Moderate** separation. Linear probe extracts meaningful boundary.

---
## Task B: Magnitude Tier Classification (Pre-earthquake only)

| Metric | Mean (5-fold) | Std |
|--------|---------------|-----|
| AUROC (OvR weighted) | 0.5784 | 0.0306 |
| Balanced Accuracy | 0.4187 | 0.0457 |
| Weighted F1 | 0.3650 | 0.0493 |

**Interpretation:** 
Balanced accuracy ~41.9% vs random 33.3% — Signal weak but present.

### Full-dataset Classification Report (Task B)
```
              precision    recall  f1-score   support

       M<5.5       0.39      0.14      0.21       616
    M5.5-6.0       0.37      0.72      0.49       518
       M>6.0       0.48      0.38      0.43       494

    accuracy                           0.40      1628
   macro avg       0.42      0.42      0.38      1628
weighted avg       0.41      0.40      0.37      1628

```