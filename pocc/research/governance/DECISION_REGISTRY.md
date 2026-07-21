# Decision Registry — LAWS V2

## Purpose
Structured tracking of key decisions with full audit trail. Each decision tracked independently of Decision Log (chronological) — this registry is organized by decision type.

## Decision Types
- **ARCH**: Architecture
- **SCIENCE**: Scientific method
- **OPS**: Operations
- **MODEL**: Model configuration
- **ORR**: Operations Readiness Review
- **PUB**: Publication / research

---

## Registry

### Decision-001 | Z/H Ratio as Primary Precursor
| Field | Value |
|---|---|
| **Type** | SCIENCE |
| **Date** | 2025-06 |
| **Decision** | Use Z/H (polarization) ratio as primary precursor indicator |
| **Reason** | Physically interpretable, established in literature, computationally efficient |
| **Alternative A** | Pure CNN on raw time series (rejected: no physical grounding) |
| **Alternative B** | EMF-only approach (rejected: insufficient station coverage) |
| **Evidence** | Rohadi et al. 2013; historical QG anomalies in Indonesian data |
| **Risk** | Medium — may miss non-QG precursors |
| **Mitigation** | Ensemble with PC3 and CWT |
| **Approver** | System Architect + Geophysicist |
| **Status** | ACTIVE |

### Decision-002 | Model Freeze for ORR
| Field | Value |
|---|---|
| **Type** | MODEL |
| **Date** | 2026-07-18 |
| **Decision** | Freeze LAWSV95Real weights and architecture for ORR evaluation |
| **Reason** | Reproducibility requirement for ORR and blind test |
| **Alternative A** | Continue tuning during ORR (rejected: breaks reproducibility) |
| **Alternative B** | Multiple model versions in parallel (rejected: too complex) |
| **Evidence** | EPEF Specification V1.0, ORR Protocol |
| **Risk** | Low — model already performing well |
| **Mitigation** | Previous versions archived in model registry |
| **Approver** | ML Lead |
| **Status** | ACTIVE |

### Decision-003 | ORR Verdict: GO WITH CONDITIONS
| Field | Value |
|---|---|
| **Type** | ORR |
| **Date** | 2026-07-20 |
| **Decision** | Conditional GO: 20 corrective actions, 2 critical items resolved |
| **Reason** | Predictor verified loaded, validation pipeline now working, ORR score 53.35/100 |
| **Alternative A** | NO-GO (rejected: would have required complete rebuild) |
| **Alternative B** | Full GO without conditions (rejected: insufficient evidence) |
| **Evidence** | ORR_01-04 reports, /api/predictor live response, validation_worker fix |
| **Risk** | Medium — 18 corrective actions still open |
| **Mitigation** | Pilot operation with monitoring |
| **Approver** | ORR Panel |
| **Status** | ACTIVE |

### Decision-004 | PatchTST as Primary Benchmark
| Field | Value |
|---|---|
| **Type** | SCIENCE |
| **Date** | 2026-07-21 |
| **Decision** | Include PatchTST in benchmark comparison suite |
| **Reason** | State-of-the-art time series forecasting, patching mechanism relevant for geophysical data |
| **Alternative A** | Vanilla Transformer (included as secondary baseline) |
| **Alternative B** | TFT (Temporal Fusion Transformer, rejected: overkill for binary classification) |
| **Evidence** | Nie et al. 2023; M4 competition results |
| **Risk** | Low — comparison only |
| **Mitigation** | Same evaluation protocol (EPEF) for all models |
| **Approver** | Research Lead |
| **Status** | PLANNED |

### Decision-005 | Change Freeze During ORR
| Field | Value |
|---|---|
| **Type** | OPS |
| **Date** | 2026-07-18 |
| **Decision** | Freeze all production changes during ORR checkpoints |
| **Reason** | Ensure stable baseline for verification runs |
| **Alternative A** | Allow hotfixes only (rejected: defeats purpose of freeze) |
| **Alternative B** | No freeze, continuous deployment (rejected: breaks ORR methodology) |
| **Evidence** | Configuration Management Plan, NASA FRR precedent |
| **Risk** | Medium — bugs cannot be fixed during ORR |
| **Mitigation** | Emergency change process for P0 incidents |
| **Approver** | Project Lead + CCB |
| **Status** | ACTIVE |
