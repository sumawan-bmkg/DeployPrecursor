# Decision Log — LAWS V2

## Purpose
Chronological record of key technical and scientific decisions with rationale, alternatives considered, and evidence.

## Log Format
```
[DATE] [ID] [TITLE]
Decision: [What was decided]
Rationale: [Why]
Alternatives: [What else was considered]
Evidence: [Data/artifacts supporting the decision]
Approved by: [Who]
```

---

## Decisions

### D-001 | Use QG Index as Primary Precursor
- **Date**: 2025-06
- **Decision**: Implement Quasi-Geomagnetic (Z/H ratio) as primary precursor method
- **Rationale**: Established in literature (Rohadi et al.), physically interpretable, computationally efficient
- **Alternatives**: Pure ML approach (rejected: no physical grounding), EMF-only (rejected: insufficient coverage)
- **Evidence**: Rohadi et al. 2013, historical QG anomalies in Indonesian data
- **Approved by**: System Architect, Geophysicist

### D-002 | Ensemble Architecture (QG + PC3 + CWT)
- **Date**: 2025-08
- **Decision**: Use ensemble of 3 methods instead of single model
- **Rationale**: Diverse precursors capture different physical phenomena; ensemble reduces variance
- **Alternatives**: Single CNN model (rejected: lower interpretability), 2-method ensemble (rejected: less diversity)
- **Evidence**: Ensemble methods literature, preliminary experiments on Indonesian data
- **Approved by**: ML Lead, System Architect

### D-003 | Decision Thresholds (0.40/0.70/0.90)
- **Date**: 2025-10
- **Decision**: Three-tier probability thresholds for ADVISORY/WATCH/WARNING
- **Rationale**: Matches BMKG alert system, allows graduated response
- **Alternatives**: Binary threshold (rejected: too coarse), 5-level system (rejected: operational complexity)
- **Evidence**: BMKG operational procedures, international EEW standards
- **Approved by**: BMKG Rep, System Architect

### D-004 | PostgreSQL Over MongoDB
- **Date**: 2025-12
- **Decision**: Use PostgreSQL 16 for all persistent storage
- **Rationale**: ACID compliance, JSONB for flexible schemas, mature backup tools
- **Alternatives**: MongoDB (rejected: weak consistency), SQLite (rejected: no concurrency), InfluxDB (rejected: limited relational)
- **Evidence**: Production requirements, team expertise, BMKG IT standards
- **Approved by**: DB Architect, System Architect

### D-005 | ORR Methodology (FRR-style)
- **Date**: 2026-07
- **Decision**: Apply NASA FRR-style Operations Readiness Review
- **Rationale**: Evidence-based, systematic, precedent in safety-critical systems
- **Alternatives**: Checklist-only (rejected: insufficient rigor), ISO 9001 audit (rejected: not designed for ML)
- **Evidence**: NASA FRR procedures, ESA ORR practices, Google SRE production readiness
- **Approved by**: Project Lead, Panel

### D-006 | 500km Spatial Fusion Radius
- **Date**: 2025-11
- **Decision**: Use 500km haversine radius for station fusion
- **Rationale**: Matches BMKG seismic network density, captures regional precursor signals
- **Alternatives**: 200km (rejected: too few stations per event), 1000km (rejected: too much spatial noise)
- **Evidence**: Indonesian station map analysis, preliminary fusion experiments
- **Approved by**: Geophysicist, ML Lead

### D-007 | CF-01 Fix (Dashboard Label Bug)
- **Date**: 2026-07-20
- **Decision**: Replace hardcoded "MOCK" with dynamic `Path.exists()` check
- **Rationale**: Predictor verified loaded via /api/predictor; only label was wrong
- **Alternatives**: Hardcode "ACTIVE" (rejected: fragile), full state machine (rejected: overkill)
- **Evidence**: /api/predictor response `status="loaded"`, /api/overview showing `"MOCK"`
- **Approved by**: System Architect

### D-008 | CF-02 Fix (CRC32 Module)
- **Date**: 2026-07-20
- **Decision**: Replace `hashlib.crc32()` with `zlib.crc32()`
- **Rationale**: CRC32 is in zlib module, not hashlib; validation worker was failing every cycle
- **Alternatives**: Custom CRC32 implementation (rejected: stdlib exists), hashlib workaround (rejected: wrong module)
- **Evidence**: Python stdlib documentation, production log showing `hashlib has no attribute crc32`
- **Approved by**: System Architect, DevOps Lead
