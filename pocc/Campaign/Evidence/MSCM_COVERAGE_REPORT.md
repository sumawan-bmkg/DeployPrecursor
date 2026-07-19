# MSCM Coverage Report

**Generated:** 2026-07-16
**Total Claims:** 18

---

## Status Summary

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Verified | 5 | 27.8% |
| 🔄 Pending Evidence | 2 | 11.1% |
| ⏳ Not Yet Evaluated | 11 | 61.1% |
| ❌ Rejected | 0 | 0% |

---

## Per-Category Coverage

### Engineering Claims (4)

| # | Claim | Status | Evidence |
|---|-------|--------|----------|
| C09 | Evidence chain complete | ✅ | FOAC cert, master manifest |
| C11 | Blind test prevents leakage | ✅ | SBTP v2.0, freeze policy |
| C12 | Deployment safe/reversible | ✅ | PDM, SHA256 manifest |
| C13 | Governance tracks changes | 🔄 | CEPSL active |

### Operational Claims (1)

| # | Claim | Status | Evidence |
|---|-------|--------|----------|
| C03 | System operates ≥14 days | 🔄 | Day 1/14 |

### Scientific Claims (13 - require blind test)

| # | Claim | Status | Evidence Needed |
|---|-------|--------|----------------|
| C01 | Anomalies precede M≥4 | ⏳ | Blind test → ROC, AUC, F1 |
| C02 | CNN+GNN outperforms baselines | ⏳ | Blind test → McNemar test |
| C04 | Pipeline deterministic | ⏳ | Server verification |
| C05 | Explanations are physical | ⏳ | Blind test → attribution |
| C06 | Physics consistency verified | ⏳ | Blind test → Z/H, polarization |
| C07 | False alarms characterized | ⏳ | Blind test → FAR by Dst/time |
| C08 | EEJ identified and mitigated | ✅ | EEJ classification report |
| C10 | Model generalizes across stations | ⏳ | Blind test → per-station metrics |
| C14 | Model calibration reliable | ⏳ | Blind test → ECE/reliability |
| C15 | Sensitivity documented | ⏳ | Blind test → parameter sweep |
| C16 | Dst/Kp correlation low | ⏳ | Blind test → regression |
| C17 | Disturbance context per prediction | ✅ | Geomagnetic disturbance dataset |
| C18 | Lead time characterized | ⏳ | Blind test → histogram |

---

## Thesis Chapter Coverage

| Chapter | Claims | Coverage |
|---------|--------|----------|
| Introduction | C01, C09, C11 | 3/3 ✅ |
| Methods — System | C12, C13 | 2/2 ✅ |
| Methods — Data | C08, C17 | 2/2 ✅ |
| Methods — Model | C02 | 1/1 ✅ |
| Methods — Protocol | C11 | 1/1 ✅ |
| Results — Primary | C01, C02, C10, C14, C15, C18 | 0/6 ⏳ |
| Results — Physics | C06, C16 | 0/2 ⏳ |
| Results — False Alarms | C07 | 0/1 ⏳ |
| Results — Explainability | C05 | 0/1 ⏳ |
| Discussion | C03, C04, C08, C09 | 2/4 🔄 |
| Conclusion | All ✅ completed | 5/18 ✅ |

---

## Paper Section Coverage

Same mapping applies. The Results section is the critical gap — all 6 primary result claims are **Not Yet Evaluated** pending blind test.

---

## Next Action

- 🔄 claims progress automatically with time (OSC, CEPSL)
- ⏳ claims transition only after blind test completion
- First post-BT action: run evaluation pipeline → fill EV-TBD files → update MSCM
