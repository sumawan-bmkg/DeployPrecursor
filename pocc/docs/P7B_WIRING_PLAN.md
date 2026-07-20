# P7B - Operational Wiring

3 tasks, no new features. Wire existing pipeline into continuous operation.

---

## Task 1 - InferenceWorker

Wire LAWS V2 inference into scheduler after Validation.

### Pipeline

```
Discovery (300s) -> Download (600s) -> Validation (60s)
                                            |
                                     INFERENCE WORKER (60s)
                                            |
                                     RuntimeTrigger (60s)
                                            |
                                     Audit (3600s)
```

### InferenceWorker per validated file:
1. Scan PDAC `events/` for `*_valid.json` files not yet processed
2. Preprocess via existing ScientificQG
3. `LAWSRealPredictor.predict()` -> `Prediction`
4. `DecisionEngine.evaluate()` -> `Decision`
5. `StationFusion.fuse()` -> `FusedEvent`
6. `EventManager.process_fused_event()` -> `Event`
7. `WarningManager.issue_warning()` -> `Warning`
8. Store to PostgreSQL
9. Mark processed (`.inferred` flag file)

### Files
- **NEW** `collector/inference_worker.py`
- **MODIFY** `collector/__main__.py` - register worker at 60s

---

## Task 2 - PostgreSQL Persistent Storage

PG 16 installed. Need `bmkg` role + `pocc` database.

### Schema (5 tables)
- `predictions`
- `decisions`
- `fused_events`
- `events`
- `warnings`

### Files
- **NEW** `collector/db.py` - PG connection pool + CRUD
- **MODIFY** `collector/event_manager.py` - add PG persistence
- **MODIFY** `collector/warning_manager.py` - add PG persistence
- **MODIFY** `collector/decision_engine.py` - add PG persistence
- **MODIFY** `backend/main.py` - API routes read from PG

---

## Task 3 - Daily Evidence Builder

Cron-style at midnight (86400s).

### Output per day:
```
/opt/pimes/laws/runtime/validation/pdac/daily_evidence/YYYY-MM-DD/
  daily_shadow_report.json
  metrics.json
  drift.json
  events.json
  warnings.json
  prediction_summary.json
```

### Files
- **NEW** `collector/daily_evidence_builder.py`

---

## Verification
1. `SELECT * FROM events;` returns data
2. Collector log shows `inference` worker active
3. Daily evidence dir appears after run
4. API endpoints read from PostgreSQL
