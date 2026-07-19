# SEOS Architecture Document

## Overview

Scientific Evidence Operating System (SEOS) v1.0
Single Source of Scientific Truth for PIMES BMKG.

## Architecture

```
validation/seos/
    config.py          — paths, weights, thresholds
    utils.py           — SSH, hashing, logging
    provenance.py      — artifact lineage (parent-child DAG)
    fingerprint.py     — hash chain per pipeline stage
    ledger.py          — append-only SQLite (no UPDATE/DELETE)
    evidence_db.py     — structured evidence with UUID+SHA256
    recommendation.py  — evidence-based recommendations
    accreditation.py   — Scientific Accreditation Index (SAI)
    run.py             — orchestrator
```

## Principles

1. **Append-Only**: Ledger never updates or deletes records
2. **UUID + SHA256**: Every evidence entry is traceable
3. **Chain of Custody**: Provenance links every artifact to its source
4. **Fingerprint Chain**: Hash chain detects any pipeline tampering
5. **Evidence-Based**: Recommendations derived from live data, never hardcoded

## Data Flow

```
Collector → Raw Data → Provenance Artifact
Pipeline  → Stage Data → Fingerprint Chain
CSQ       → Scores → Evidence Database
Drift     → Analysis → Recommendations
All       → Ledger (append-only)
SAI       → Accreditation Certificate
```

## Milestones

- M1: Provenance + Fingerprint + Ledger + Evidence + SAI ✅
- M2: Continuous Qualification + Drift Intelligence (extends CSQ)
- M3: Living ERB + Recommendation Engine
- M4: Prediction Replay + Scientific Digital Twin
- M5: Scientific Dashboard + Final Acceptance
