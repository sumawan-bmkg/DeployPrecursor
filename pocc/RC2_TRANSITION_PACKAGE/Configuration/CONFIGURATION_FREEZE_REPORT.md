# WP2 — Configuration Freeze Report

**Generated:** 2026-07-16

## Frozen Configurations

| Component | Path | Status |
|-----------|------|--------|
| BOCC server | `pocc/backend/main.py` | FROZEN — v2.0.0-rc2 |
| Collector scheduler | `pocc/collector/scheduler_engine.py` | FROZEN |
| OSC cron | `crontab -l` (server) | ACTIVE — hourly + daily |
| CEPSL lock | `posc/osc/data/cepsl_status.json` | ACTIVE — append-only |
| Prior models | `laws/priors/prior_*.pt` | FROZEN — 21 stations |
| Station signatures | `laws/runtime/validation/rdmc/artifacts/` | FROZEN — 28 stations |
| Deploy scripts | `pocc/deploy.py` | FROZEN |
| Port config | Port 8500 (production), 8501 (blue-green) | FROZEN |
| Host | 10.20.229.43 | FROZEN |
| Python runtime | `.venv` Python 3.12 | FROZEN |

## Configuration Manifest

All configuration files have been SHA256-logged in `PRODUCTION_FREEZE_20260716.json`.

## Change Control

Any configuration change after this freeze requires:
1. UUID
2. Reason
3. SHA256 before/after
4. Approval log
5. Rollback plan
