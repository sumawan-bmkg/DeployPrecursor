# Dissertation Defense Binder

**Version:** v2.0.0-rc2-freeze
**Date:** 2026-07-16
**Purpose:** One claim → one evidence → one figure → one table → one reference → one evidence location

---

## How to Use This Binder

For each examination question, the candidate follows this chain:
1. Identify which claim is being challenged
2. Locate the evidence package that supports the claim
3. Show the figure/table that visualizes the evidence
4. Cite the reference
5. Provide the evidence file location

---

## Claim 1: ULF Anomalies Can Be Detected in Real Time

| Element | Location |
|---------|----------|
| Figure | Dashboard screenshot (Figure 3) |
| Table | Collector status from daily report |
| Evidence | OSC hourly logs, `/opt/pimes/logs/collector/` |
| Reference | Hayakawa et al. (1996), Hattori et al. (2004) |
| Location | `Campaign/Daily/` + `RC2_TRANSITION_PACKAGE/Runbooks/OPERATOR_HANDBOOK.md` |

---

## Claim 2: Graph Neural Networks Improve Detection Over Single-Station Models

| Element | Location |
|---------|----------|
| Figure | Null model comparison bar chart (Figure 14) |
| Table | Primary results table (Table 1) — CNN-1D vs CNN+GNN rows |
| Evidence | `BLIND_TEST_PACKAGE/v2/BASELINE_COMPARISON_PROTOCOL.md` |
| Reference | Scarselli et al. (2009), Kipf & Welling (2017) |
| Location | `Campaign/Evaluation/` + paper-gji branch |

---

## Claim 3: The System Achieves F1 > 0.74 on Blind Test Data

| Element | Location |
|---------|----------|
| Figure | ROC curve (Figure 5), PR curve (Figure 6) |
| Table | Primary results table (Table 1) — proposed model row |
| Evidence | `Campaign/Blind_Test/prediction_registry.csv` |
| Reference | SBTP v2.0 evaluation protocol |
| Location | `Campaign/Evaluation/` + `pocc/BLIND_TEST_LEDGER/` |

---

## Claim 4: Predictions Are Physically Consistent with ULF Precursor Theory

| Element | Location |
|---------|----------|
| Figure | Physics validation panel (Figure 11) |
| Table | Stratified results by Dst (Table 3) |
| Evidence | `Campaign/Evidence/PHYSICS_VALIDATION_PROTOCOL.md` |
| Reference | Hayakawa et al. (1996), Fraser-Smith (2008) |
| Location | `Campaign/Evidence/` |

---

## Claim 5: The Platform Is Operationally Stable

| Element | Location |
|---------|----------|
| Figure | Campaign timeline (Figure 13) |
| Table | Daily campaign success > 99% |
| Evidence | OSC snapshots, CEPSL ledger |
| Reference | `pocc/RC2_TRANSITION_PACKAGE/` |
| Location | `/opt/pimes/posc/osc/data/` + `Campaign/Daily/` |

---

## Claim 6: The Model Generalizes Across Stations

| Element | Location |
|---------|----------|
| Figure | Station attribution heatmap (Figure 10) |
| Table | Per-station results (Table 2) |
| Evidence | Station-specific metrics from evaluation |
| Location | `Campaign/Evaluation/` |

---

## Claim 7: The Results Are Reproducible

| Element | Location |
|---------|----------|
| Figure | Deterministic reproducibility test (run inference twice, compare output) |
| Table | Environment freeze + seed documentation |
| Evidence | `pocc/REPRODUCIBILITY_BOOK/REPRODUCIBILITY_BOOK.md` |
| Reference | GJI data availability requirements |
| Location | `Campaign/Publication/` + `BLIND_TEST_PACKAGE/v2/REPRODUCIBILITY_PROTOCOL.md` |

---

## Claim 8: False Alarms Are Well-Characterized

| Element | Location |
|---------|----------|
| Figure | FP characterization (Figure 12) |
| Table | Stratified FAR by Dst, time-of-day, EEJ zone |
| Evidence | `Campaign/Evidence/FALSE_ALARM_PROTOCOL.md` |
| Location | `Campaign/Evaluation/` |

---

## Claim 9: EEJ Contamination Is Acknowledged and Mitigated

| Element | Location |
|---------|----------|
| Figure | EEJ station map (Figure S3) |
| Table | EEJ classification (core/transition/non-EEJ) |
| Evidence | `Campaign/Evidence/EEJ_CLASSIFICATION_REPORT.md` |
| Location | `Campaign/Evidence/` |

---

## Claim 10: The Evidence Chain Is Complete and Auditable

| Element | Location |
|---------|----------|
| Figure | Evidence chain diagram (from BLIND_TEST_EVIDENCE_SPECIFICATION.md) |
| Table | Master Evidence Manifest (40 items indexed) |
| Evidence | `PIMES_SCIENTIFIC_DATA_BOOK/MASTER_EVIDENCE_MANIFEST.json` |
| Reference | FOAC acceptance certificate |
| Location | `pocc/PIMES_SCIENTIFIC_DATA_BOOK/` + `pocc/RC2_TRANSITION_PACKAGE/Certificates/` |

---

## Cross-Reference: Audit Questions to Claim Map

| Audit Question (from 90-question simulation) | Claim | Evidence Location |
|---------------------------------------------|-------|-------------------|
| A1: External field separation | Claim 4, Claim 9 | `Campaign/Evidence/EEJ_CLASSIFICATION_REPORT.md` |
| A5: Expected SNR for M5 vs M8 | Claim 3, Claim 4 | Physics validation results |
| B5: Retrospective validation | Claim 3 | Wait: INSUFFICIENT EVIDENCE — 2018-2019 catalog not available |
| C6: Baseline removal strategy | Claim 4 | Preprocessing documentation |
| E1: Rollback strategy | Claim 5 | `pocc/deploy.py` + `RC2_TRANSITION_PACKAGE/Deployment/DEPLOYMENT_HARDENING_REPORT.md` |
| F1: Third-party reproducibility | Claim 7 | `pocc/REPRODUCIBILITY_BOOK/` |
| H1: Why blind test is blind | Claim 3 | `v2.0.0-rc2-freeze` tag predates 2025-2026 data |
| I1: Why F1 vs MCC | Claim 3 | Both reported in evaluation |
| J1: Data availability | Claim 7 | BMKG data restrictions documented |

---

## Structure for Physical Binder

Tab 1: System Overview (Figures 1-4, Claim 1)
Tab 2: Results (Figures 5-9, Tables 1-2, Claim 3)
Tab 3: Validation (Figures 10-14, Tables 3-4, Claims 2,4,6,8)
Tab 4: Reproducibility (Claim 7, Environment lock)
Tab 5: Evidence Chain (Claim 10, Master Manifest)
Tab 6: Limitations (EEJ, data dependency, burn-in gap)
Tab 7: Appendices (Supplementary figures, audit results)
