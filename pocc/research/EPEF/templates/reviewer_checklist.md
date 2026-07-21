# Reviewer Checklist — EPEF V1.0

## Checklist Items
Each item: PASS / FAIL / NOT EVALUATED

### A. Dataset & Preprocessing (6 items)
- [ ] A1. Dataset provenance documented
- [ ] A2. Dataset freeze hash verified
- [ ] A3. Preprocessing pipeline documented
- [ ] A4. Data quality assessment performed
- [ ] A5. No data leakage between train/test
- [ ] A6. Station metadata complete

### B. Model & Inference (5 items)
- [ ] B1. Model weights frozen
- [ ] B2. Inference deterministic (seed fixed)
- [ ] B3. Prediction schema validated
- [ ] B4. Fallback mechanism defined
- [ ] B5. Error handling documented

### C. Evaluation Methodology (6 items)
- [ ] C1. Blind test protocol followed
- [ ] C2. Metrics computed correctly
- [ ] C3. Statistical significance assessed
- [ ] C4. Baseline comparison performed
- [ ] C5. Calibration reported
- [ ] C6. Lead time analyzed

### D. Operational Readiness (5 items)
- [ ] D1. ORR completed (score >= 50)
- [ ] D2. All CF items closed
- [ ] D3. Burn-in evidence collected
- [ ] D4. SOPs in place
- [ ] D5. Incident response defined

## Overall Verdict
| Criterion | Required | Met |
|---|---|---|
| All A items PASS | Yes | |
| All B items PASS | Yes | |
| All C items PASS | Yes | |
| All D items PASS | Yes | |

**FINAL VERDICT**: GO / CONDITIONAL GO / NO-GO
