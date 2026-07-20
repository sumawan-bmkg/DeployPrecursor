# LAWS V2 — Refined Implementation Plan

## Architecture Decisions (Approved)

| # | Decision | Choice |
|---|----------|--------|
| 1 | Existing raw files | Legacy read-only at `/opt/pimes/data/raw/` — no migration |
| 2 | Storage endpoint | Extend existing health/status (not `/api/storage`) |
| 3 | Deployment | Progressive (7 phases), no big bang |
| 4 | Artifact management | ArtifactManager (centralized, not per-worker) |
| 5 | Lifecycle Registry | Add dependency graph (artifact lineage) |
| 6 | Purge | Transactional: Candidate→Verify→Lock→Delete→Audit→Unlock |
| 7 | Storage budgeting | StorageBudgetManager with tier limits + pressure purge |

## NEW Components (refined)

### `pocc/collector/lifecycle_registry.py`
State machine + dependency graph.
- States: NEW → DOWNLOADED → VALIDATED_BINARY → VALIDATED_SCIENTIFIC → PARSED → PREPROCESSED → HDF5_CREATED → HDF5_VERIFIED → INFERENCE_DONE → PREDICTION_STORED → PURGED
- Failure: → QUARANTINE (with FAILED_BINARY/FAILED_QC/FAILED_PARSE/FAILED_CWT/FAILED_HDF5/FAILED_INFERENCE)
- Dependency graph: `{HDF5: [Waveform], Prediction: [HDF5], Alert: [Prediction]}` — invalidates downstream on failure
- JSON at `/opt/pimes/pocc/runtime/lifecycle_registry.json`
- `get_pending_states()` for crash recovery — resume from last state
- `transition_if(current, target)` — idempotent, crash-safe
- `get_downstream(artifact_id)` — returns dependent artifacts, their statuses

### `pocc/collector/artifact_manager.py`
Centralized artifact lifecycle.
- `register(artifact_type, station, filename, metadata)` — register new artifact
- `verify(artifact_id, checksum)` — verify integrity
- `move(artifact_id, target_path)` — move between tiers
- `archive(artifact_id)` — archive
- `delete(artifact_id)` — delete with precondition checks
- `restore(artifact_id)` — restore from archive
- Artifact types: WAVEFORM, HDF5, PREDICTION, REGISTRY, LOG, QC, AUDIT
- All operations go through lifecycle registry

### `pocc/collector/cache_manager.py`
Tiered cache for raw waveform.
- Location: `/opt/pimes/runtime/cache/raw/`
- `store(station, filename, binary)` — save to cache
- `get_path(station, filename)` — full path
- `delete_if_eligible()` — checks lifecycle registry + retention + storage budget
- `move_to_quarantine(station, filename, reason)` — quarantine path
- `size()` / `file_count()` — metrics

### `pocc/collector/quarantine_manager.py`
Failure isolation.
- `quarantine(station, filename, reason, detail)` — move to `/opt/pimes/runtime/quarantine/{reason}/`
- `list()` — all quarantined
- `size()` — total
- `auto_cleanup(days=30)` — periodic

### `pocc/collector/storage_budget_manager.py`
Budget-aware storage.
- Config: `cache_limit`, `quarantine_limit`, `hdf5_limit`, `warning%`, `critical%`
- `pressure()` — 0.0 (low) to 1.0 (critical)
- `is_eligible_for_purge()` — age + pressure
- `get_metrics()` — all tier sizes, usage %, projected full date, growth rate

### `pocc/collector/purge_worker.py`
Transactional purge service.
- Phase: Candidate → Verify → Lock → Delete → Audit → Unlock
- Lock prevents concurrent purge on same artifact
- Checks: HDF5_VERIFIED + INFERENCE_DONE + PREDICTION_STORED + no exception + retention elapsed
- Audit trail for every delete
- systemd service + timer (hourly)
- Also registered as PurgeWorker in scheduler (3600s)

### `pocc/collector/hdf5_enhanced.py`
Full metadata embedding.
- All metadata: Station, Date, UTC, UUID, SHA256, Pipeline Version, Git Commit, Processing Host, Processing Duration, QC Status, Binary Validation, Scientific Validation, Creation Timestamp, Input Filename, Model Version, Preprocessing Version
- Compression: gzip, shuffle=True, chunks=True
- SHA256 computed post-write
- Backward compatible — same tensor structure

### `pocc/collector/scientific_qg.py`
Local copy of ScientificQG v3.1 (6 levels).

### `storage_policy.yaml`
```yaml
cache:
  location: /opt/pimes/runtime/cache/raw
storage:
  cache_limit_gb: 100
  quarantine_limit_gb: 30
  hdf5_limit_gb: 500
  warning_percent: 80
  critical_percent: 90
retention:
  successful_hours: 24
  quarantine_days: 30
purge:
  enabled: false  # Phase 1-3: OFF
  verify_sha256: true
  require_prediction: true
  require_registry: true
  transactional_lock: true
```

## MODIFIED Workers

### `pocc/collector/__main__.py`
- Add PurgeWorker (3600s)
- Init lifecycle registry
- Load storage_policy.yaml
- Init ArtifactManager + StorageBudgetManager

### `pocc/collector/download_worker.py`
- Target: `/opt/pimes/runtime/cache/raw/{station}/` (new pipeline)
- Register lifecycle state: NEW → DOWNLOADED
- Register artifact via ArtifactManager

### `pocc/collector/validation_worker.py`
- Binary validation → VALIDATED_BINARY or FAILED_BINARY→QUARANTINE
- Scientific validation (ScientificQG) → VALIDATED_SCIENTIFIC or FAILED_QC→QUARANTINE

### `pocc/collector/runtime_trigger.py`
- Read lifecycle registry for INFERENCE_DONE → PREDICTION_STORED
- Use ArtifactManager for prediction artifact

### `pocc/collector/audit_worker.py`
- Storage monitoring via StorageBudgetManager
- Disk usage, growth rate, projected full
- Add to dashboard health model

## Progressive Deployment (7 Phases)

| Phase | Changes | Duration | Delete? |
|-------|---------|----------|---------|
| **P1** | Lifecycle Registry + ArtifactManager — passive monitoring only | Deploy day | OFF |
| **P2** | CacheManager — new files go to cache, delete=OFF | 1 week | OFF |
| **P3** | ScientificQG + Quarantine in validation flow | 1 cycle | OFF |
| **P4** | PurgeWorker — retention=30 days | 1 week | 30 days |
| **P5** | Retention → 7 days | 1 week | 7 days |
| **P6** | Retention → 24 hours | 2 weeks | 24h |
| **P7** | Retention → 0h (if needed) + P1-P6 proven stable | Optional | Immediate |

## Priority Matrix

| Priority | Component | Depends On | Deliverable |
|----------|-----------|------------|-------------|
| P1 | Lifecycle Registry | — | lifecycle_registry.py |
| P2 | ArtifactManager | P1 | artifact_manager.py |
| P3 | CacheManager | P1 | cache_manager.py |
| P4 | ScientificQG | P3 | scientific_qg.py |
| P5 | Quarantine Manager | P3 | quarantine_manager.py |
| P6 | Storage Budget Manager | P1 | storage_budget_manager.py |
| P7 | Purge Worker | P2+P3+P4+P5+P6 | purge_worker.py + systemd |
| P8 | Dashboard & Monitoring | All | audit_worker + backend |
| — | HDF5 Enhanced | P1 | hdf5_enhanced.py |

## Files Layout
```
pocc/collector/
├── __main__.py          [MODIFY] — register PurgeWorker, init managers
├── lifecycle_registry.py [NEW] — state machine + dep graph
├── artifact_manager.py   [NEW] — centralized artifact lifecycle
├── cache_manager.py      [NEW] — tiered cache
├── quarantine_manager.py [NEW] — failure isolation
├── storage_budget_manager.py [NEW] — budget-aware storage
├── purge_worker.py       [NEW] — transactional purge
├── hdf5_enhanced.py      [NEW] — metadata embedding
├── scientific_qg.py      [NEW] — v3.1 quality gate
├── storage_policy.yaml   [NEW] — config
├── scheduler_engine.py   [NO CHANGE]
├── download_worker.py    [MODIFY] — lifecycle + cache
├── validation_worker.py  [MODIFY] — ScientificQG integration
├── runtime_trigger.py    [MODIFY] — lifecycle states
├── audit_worker.py       [MODIFY] — storage metrics
├── discovery_worker.py   [NO CHANGE]
└── rawdata_worker.py     [NO CHANGE]

deploy/systemd/
├── laws-purge.service    [NEW]
└── laws-purge.timer      [NEW]

pocc/docs/v2/
├── STATELESS_PIPELINE_DESIGN.md
├── DATA_LIFECYCLE_SPECIFICATION.md
├── SCIENTIFIC_QG_SPECIFICATION.md
├── STORAGE_POLICY.md
├── PURGE_SERVICE.md
├── RECOVERY_STRATEGY.md
├── PERFORMANCE_BENCHMARK.md
├── DISK_USAGE_REPORT.md
├── BACKWARD_COMPATIBILITY_REPORT.md
└── IMPLEMENTATION_DIFF.md
```

## Verification
- Pre: syntax check, schema validation, backward-compat HDF5 test
- Post-phase: each phase has verification criteria before next phase
- Test 1-8 as before, executed progressively per phase
