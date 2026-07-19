# Master Scientific Claim Matrix (MSCM)

**Version:** v2.0.0-rc2-freeze
**Generated:** 2026-07-16
**Purpose:** Every sentence in the dissertation/paper traces to one row in this matrix.

---

## Status Taxonomy

Every claim has exactly one of four status values:

| Status | Definition | Example |
|--------|-----------|---------|
| ✅ **Verified** | Supported by empirical evidence collected and analyzed | C12: Deployment safety — evidence from PDM logs |
| 🔄 **Pending Evidence** | Protocol ready, evidence being collected | C03: OSC stability — running day-by-day |
| ⏳ **Not Yet Evaluated** | Cannot evaluate because data not available | C01: Blind test claims — need BMKG waveform |
| ❌ **Rejected** | Blind test results did not support claim | (reserved for after blind test analysis) |

---

## Claims

| # | Claim | Evidence ID | Figure | Table | Statistical Test | Source | Status |
|---|-------|-------------|--------|-------|-----------------|--------|--------|
| C01 | ULF anomalies precede M≥4 earthquakes in Indonesia | EV-TBD | Fig 5 (ROC), Fig 6 (PR) | Table 1 (Primary) | AUC, p < 0.05 | Blind Test | ⏳ Pending |
| C02 | CNN+GNN outperforms single-station baselines | EV-TBD | Fig 14 (Null comparison) | Table 1 (Primary) | McNemar, p < 0.05 | Blind Test | ⏳ Pending |
| C03 | System operates continuously for ≥14 days | EV-001 (OSC logs) | Fig 3 (Dashboard) | Table 1 (Uptime) | Uptime > 99% | OSC | 🔄 Pending Evidence |
| C04 | Predictions are reproducible and deterministic | EV-035 (Repro book) | — | Table 3 (Seeds) | SHA256 match | Reproducibility | ⏳ Not Yet Evaluated |
| C05 | Model explanations identify physically meaningful features | EV-107 (Explain) | Fig 10 (Station attr) | Table 8 (Per-station) | Attribution scores | SBTP v2.0 | ⏳ Not Yet Evaluated |
| C06 | Predictions are physically consistent with ULF precursor theory | EV-120 (Physics) | Fig 11 (Physics panel) | Table 10 (Z/H) | Z/H > quiet baseline | Physics Audit | ⏳ Not Yet Evaluated |
| C07 | False alarms are characterized and non-seismic | EV-110 (FA protocol) | Fig 12 (FP char) | Table 9 (Stratified FAR) | FAR(storm) vs FAR(quiet) | SBTP v2.0 | ⏳ Pending |
| C08 | EEJ contamination is identified and mitigated | EV-115 (EEJ report) | Fig S3 (EEJ map) | Table 11 (EEJ stratified) | Day/night FAR ratio | EEJ Report | ✅ Verified |
| C09 | Evidence chain is complete and auditable | EV-023 (Certificate) | Fig 1 (Architecture) | Table 12 (Evidence atlas) | SHA256 manifest | FOAC | ✅ Verified |
| C10 | Model generalizes across 21 Indonesian stations | EV-TBD | Fig 10 (Station heatmap) | Table 2 (Per-station) | Station-specific F1 | Blind Test | ⏳ Not Yet Evaluated |
| C11 | Blind test protocol prevents data leakage | EV-036 (SBTP v2) | Fig 13 (Timeline) | — | `v2.0.0-rc2-freeze` tag | SBTP v2.0 | ✅ Complete |
| C12 | Deployment is safe, verifiable, and reversible | EV-024 (Freeze manifest) | — | Table 4 (Deploy metrics) | SHA256 verify | PDM | ✅ Complete |
| C13 | Platform governance tracks all changes | EV-002 (CEPSL) | — | — | SHA256 chain | Governance | ✅ Active |
| C14 | Model calibration is reliable | EV-TBD | Fig 7 (Calibration) | Table 5 (ECE/MCE) | ECE < 0.10 | Blind Test | ⏳ Pending |
| C15 | Sensitivity to parameters is documented | EV-TBD | — | Table 6 (Sensitivity) | F1 stability across ranges | Blind Test | ⏳ Pending |
| C16 | Dst/Kp correlation is low | EV-TBD | Fig 11c (Dst scatter) | Table 7 (Dst stratified) | |r| < 0.3 | Physics Audit | ⏳ Pending |
| C17 | Geomagnetic disturbance context per prediction | EV-118 (Disturbance dataset) | — | Table 13 (Disturbance) | Dst-stratified FAR | Campaign | ✅ Verified |
| C18 | Lead time distribution is characterized | EV-TBD | Fig 9 (Lead time) | Table 1 (Lead time) | Mean ± SD | Blind Test | ⏳ Not Yet Evaluated |

---

## Evidence Requirements

| Claim | Evidence Required | Type | Collection Method |
|-------|-------------------|------|-------------------|
| C01-C02, C10, C14-C15, C18 | Blind test results | Quantitative | Automated evaluation pipeline |
| C03 | OSC logs, health check | Time series | Daily snapshot |
| C04 | `diff` of two inference runs | Verification | Manual test on server |
| C05 | Attribution outputs per prediction | Diagnostic | Explainability pipeline |
| C06 | H/Z, polarization, spectral analysis | Diagnostic | Physics validation pipeline |
| C07 | FAR by Dst/time-of-day/season | Quantitative | Evaluation pipeline |
| C08 | Magnetic latitude, diurnal FAR | Diagnostic | Geomagnetic computation |
| C09 | SHA256 manifest, evidence atlas | Metadata | Already collected |
| C11 | Git tag, freeze policy | Metadata | Already documented |
| C12 | Deploy logs, health checks | Operational | PDM |
| C13 | CEPSL snapshots | Time series | Already running |
| C16 | Dst/Kp regression | Quantitative | Evaluation pipeline |
| C17 | Disturbance context table | Reference | Already documented |

---

## Traceability to Dissertation/Paper Sections

| Paper Section | Claims Used |
|---------------|-------------|
| Introduction | C01, C09, C11 |
| Methods — System | C12, C13 |
| Methods — Data | C08, C17 |
| Methods — Model | C02 |
| Methods — Protocol | C11 |
| Results — Primary | C01, C02, C10, C14, C15, C18 |
| Results — Physics | C06, C16 |
| Results — False Alarms | C07 |
| Results — Explainability | C05 |
| Discussion | C03, C04, C08, C09 |
| Limitations | All ⏳ pending claims |
| Conclusion | All ✅ completed claims |

---

## Status Legend

| Status | Meaning |
|--------|---------|
| ✅ Verified | Empirical evidence collected and supports claim |
| 🔄 Pending Evidence | Protocol ready, evidence being collected now |
| ⏳ Not Yet Evaluated | Requires blind test data — not yet evaluable |
| ❌ Rejected | Evidence contradicts claim (reserved) |
