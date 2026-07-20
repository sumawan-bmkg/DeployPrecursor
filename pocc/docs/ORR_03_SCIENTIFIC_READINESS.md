# ORR-03 — Scientific & Model Readiness Review
## LAWS V2 Operational Shadow — Operations Readiness Review

---

> **Document Control**
>
> | Field | Value |
> |-------|-------|
> | Document ID | LAWS-V2-ORR-03 |
> | Title | Scientific & Model Readiness Review |
> | System | LAWS V2 Operational Shadow |
> | Review Date | 2026-07-20 |
> | Review Type | Independent Operations Readiness Review |
> | Review Panel | Senior Geophysicist + AI/ML Engineer + Chief System Architect |

---

> [!WARNING]
> **CRITICAL DISCLAIMER**
>
> This review assesses the scientific pipeline components that are **designed and coded** but **have not been verified** with production data.
>
> The system is currently running in **MOCK predictor mode** with **no real predictions** generated. All scientific pipeline stages downstream (PC3, CWT, scalogram, inference) are **unvalidated in the deployed environment**.
>
> **Scientific readiness cannot be confirmed until real predictions are flowing and validated against ground-truth earthquake catalogs.**

---

## Executive Summary

The LAWS V2 scientific pipeline has been **architecturally designed** with the correct components for an earthquake precursor monitoring system. However, **none of the scientific pipeline has been verified in production**:

1. **All ScientificQG/PC3/CWT/scalogram** modules exist but have not been observed processing real data
2. **LAWS V9.5 predictor** is not running — system is on MOCK mode
3. **Decision thresholds** are documented but unvalidated against real events
4. **No ground truth comparison** has been performed
5. **No null distribution** exists to establish baseline noise levels
6. **Scientific score**: 0.0% (reported by live system)

**Verdict: NOT READY — Scientific pipeline requires verification with real data.**

---

## Phase 12 — Scientific Review

### 12.1 Scientific Pipeline Architecture

```mermaid
graph LR
    RAW[Raw magnetometer<br/>1-second samples] --> QG[ScientificQG<br/>Quality Control]
    QG --> PC3[PC3 Bandpass<br/>10-45s period]
    PC3 --> CWT[CWT Transform<br/>Wavelet analysis]
    CWT --> SCALO[Scalogram<br/>Time-frequency map]
    SCALO --> LAWS[LAWS V9.5<br/>Deep Learning Model]
    LAWS --> PRED[Prediction<br/>Probability + Location]
    PRED --> DECIDE[Decision Engine<br/>4 Rule Gates]
    DECIDE --> FUSION[Station Fusion<br/>500km/2hr window]

    style RAW fill:#1e3a5f,color:#fff
    style QG fill:#f39c12,color:#fff
    style PC3 fill:#f39c12,color:#fff
    style CWT fill:#f39c12,color:#fff
    style SCALO fill:#f39c12,color:#fff
    style LAWS fill:#7b241c,color:#fff
    style PRED fill:#7b241c,color:#fff
    style DECIDE fill:#1a5276,color:#fff
    style FUSION fill:#1a5276,color:#fff
```

> **Figure ORR3.1** — Scientific pipeline stages. Red = not verified in production. Orange = code exists but unvalidated.

### 12.2 Preprocessing Pipeline

#### ScientificQG

| Attribute | Assessment | Evidence |
|-----------|-----------|----------|
| Module exists | ✅ | `collector/scientific_qg/` directory exists |
| Purpose | QC magnetometer data | Code review |
| Input | Raw 1‑second magnetometer | Unverified |
| Output | Cleaned data | Unverified |
| Production verified | ❌ | No evidence of processing in logs |

#### PC3 Bandpass Filter

| Attribute | Assessment | Evidence |
|-----------|-----------|----------|
| Module exists | ✅ | Referenced in pipeline code |
| Purpose | Extract 10–45s period band | Code review |
| Scientific basis | Pc3 frequency range (0.02–0.1 Hz) related to ULF waves | Documented |
| Production verified | ❌ | No evidence in logs |

#### CWT Transform

| Attribute | Assessment | Evidence |
|-----------|-----------|----------|
| Module exists | ✅ | Referenced in pipeline |
| Purpose | Time-frequency transform | Code review |
| Input | PC3-filtered signal | Unverified |
| Output | Scalogram | Unverified |
| Production verified | ❌ | No evidence |

#### Scalogram Generation

| Attribute | Assessment | Evidence |
|-----------|-----------|----------|
| Module exists | ✅ | Referenced |
| Purpose | 2D time-frequency image for ML input | Code review |
| Production verified | ❌ | Not observed |

### 12.3 Prediction Model — LAWS V9.5

#### Model Assessment

| Attribute | Assessment | Evidence |
|-----------|-----------|----------|
| Model checkpoint | ✅ | Referenced in deploy scripts |
| Model version | V9.5 | Documented |
| Inference bridge | `predict_cli.py` (92 lines) | Code exists |
| Model architecture | Deep learning (unspecified) | Not reviewed |
| Training data | Historical magnetometer data | Not reviewed |
| Training period | Not documented | ❌ NOT VERIFIED |
| Validation metric | Not documented | ❌ NOT VERIFIED |
| Production inference | ❌ MOCK active | Live system evidence |

#### Model Contract (Expected vs Actual)

```python
# Expected (LAWS V9.5):
model_name = "LAWS V9.5"
backend = "cpu/gpu"

# Actual (live, 2026-07-20):
model_name = "MockPredictor"
backend = "cpu"
```

### 12.4 Decision Engine

| Rule | Threshold | Purpose | Status |
|------|-----------|---------|--------|
| ProbabilityThreshold | 0.40 / 0.70 / 0.90 | Escalate level by probability | CODE REVIEWED |
| QCConsistency | min 0.50 | Reject low-quality predictions | CODE REVIEWED |
| UncertaintyGate | max 0.50 | Reject high-uncertainty predictions | CODE REVIEWED |
| StormGate | Kp > 4 suppress | Suppress during magnetic storms | CODE REVIEWED |

**Decision Levels**:
- NORMAL (P < 0.40)
- ADVISORY (P ≥ 0.40)
- WATCH (P ≥ 0.70)
- WARNING (P ≥ 0.90)

### 12.5 Station Fusion

| Parameter | Value | Source |
|-----------|-------|--------|
| Fusion radius | 500 km | `station_fusion.py` |
| Time window | 2 hours | `station_fusion.py` |
| Min stations | 2 | `station_fusion.py` |
| Min probability | 0.40 | `station_fusion.py` |
| Distance metric | Haversine | `station_fusion.py` |
| Stations configured | 23 | `STATION_COORDS` dict |

### 12.6 Warning Manager

| Parameter | Value | Source |
|-----------|-------|--------|
| Warning levels | ADVISORY, WATCH, WARNING | `warning_manager.py` |
| State machine | NEW → ACTIVE → UPDATED → EXPIRED → VERIFIED → RETRACTED | `warning_manager.py` |
| Persistence | JSON files + PostgreSQL | Hybrid |

### 12.7 Scientific Findings

| ID | Finding | Severity | Verified |
|----|---------|----------|----------|
| SCI-01 | ScientificQG module exists but unverified in production | MAJOR | ❌ NOT VERIFIED |
| SCI-02 | PC3 bandpass filter unvalidated against known events | MAJOR | ❌ NOT VERIFIED |
| SCI-03 | CWT/scalogram unvalidated in deployed environment | MAJOR | ❌ NOT VERIFIED |
| SCI-04 | LAWS V9.5 model not running (MOCK active) | CRITICAL | ✅ VERIFIED |
| SCI-05 | Model training history and validation metrics not documented | MAJOR | ❌ NOT VERIFIED |
| SCI-06 | Decision thresholds adopted from literature, not empirically validated | MINOR | ⚠️ PARTIAL |
| SCI-07 | Fusion parameters (500km, 2hr) not validated against BMKG catalog | MAJOR | ❌ NOT VERIFIED |
| SCI-08 | No ground truth comparison performed | CRITICAL | ❌ NOT VERIFIED |
| SCI-09 | No false alarm rate established | MAJOR | ❌ NOT VERIFIED |
| SCI-10 | No lead time distribution established | MAJOR | ❌ NOT VERIFIED |
| SCI-11 | No null distribution for probability baseline | MAJOR | ❌ NOT VERIFIED |

### 12.8 Scientific Validation Requirements

Before ORR can pass on scientific grounds, the following must be demonstrated:

```text
1. Data Flow Verification
   [ ] Raw magnetometer → ScientificQG → clean signals in evidence
   [ ] Clean signals → PC3 → bandpass signals (10-45s period)
   [ ] PC3 → CWT → time-frequency scalograms
   [ ] Scalograms → LAWS V9.5 → predictions in PostgreSQL

2. Model Validation
   [ ] Model checkpoint loads successfully
   [ ] Inference produces real (non-MOCK) predictions
   [ ] Probability distribution is non-uniform
   [ ] Latency is within operational bounds

3. Ground Truth Comparison
   [ ] 30 days of predictions compared to BMKG earthquake catalog
   [ ] ROC curve or skill score computed
   [ ] False alarm rate < threshold (TBD)
   [ ] Lead time > threshold (TBD by BMKG stakeholders)
```

### 12.9 Scientific Readiness Score

| Component | Score | Required | Verdict |
|-----------|-------|----------|---------|
| Data Pipeline | 0/100 | 70/100 | ❌ |
| Model Readiness | 0/100 | 70/100 | ❌ |
| Decision Logic | 40/100 | 70/100 | ❌ |
| Validation | 0/100 | 70/100 | ❌ |
| Ground Truth | 0/100 | 70/100 | ❌ |
| **Scientific Total** | **8/100** | **70/100** | ❌ |

---

## Scientific Open Issues

| # | Issue | Criticality | Resolution Path |
|---|-------|-------------|-----------------|
| S-01 | Activate LAWS V9.5 predictor | CRITICAL | Fix predictor routing (toggle MOCK → REAL) |
| S-02 | Verify ScientificQG with real data | CRITICAL | Run pipeline on one known event |
| S-03 | Validate PC3/CWT against known precursor | MAJOR | Compare output with published examples |
| S-04 | Establish null distribution | MAJOR | Run on 30 days of non-event data |
| S-05 | Run ground truth comparison | CRITICAL | Cross-reference with EQ catalog |
| S-06 | Document model training/validation | MAJOR | Write model card |

---

**END OF ORR-03 — Scientific & Model Readiness Review**
