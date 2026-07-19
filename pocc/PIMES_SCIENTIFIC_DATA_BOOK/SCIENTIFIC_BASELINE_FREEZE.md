# PIMES Scientific Baseline Freeze — Checklist

**Version:** v2.0.0-rc2-freeze
**Date:** 2026-07-16

## Component Freeze Verification

| Component | Path / Reference | SHA256 | Status |
|-----------|------------------|--------|--------|
| Source code | Git tag `v2.0.0-rc2-freeze` | dddbd0e → 66bead3 | FROZEN |
| Dashboard | `backend/main.py` | `2340b3d4333073bb` | FROZEN |
| Deployment manager | `deploy.py` | `a083302fc70b839d` | FROZEN |
| Templates | `backend/templates/*.html` | per manifest | FROZEN |
| Prior models (21 stations) | `laws/priors/prior_*.pt` | per file | FROZEN |
| Station signatures (28) | `laws/runtime/validation/rdmc/artifacts/` | per file | FROZEN |
| Golden dataset | `laws/runtime/validation/golden_dataset/` | per file | FROZEN |
| Apollo priors | `laws/priors/` | 68 files | FROZEN |
| RDMC artifacts | `laws/runtime/validation/rdmc/` | per file | FROZEN |
| Inference engine | `laws/runtime/inference.py` | — | FROZEN (server) |
| RuntimeKernel | `laws/runtime/` | — | FROZEN (server) |
| Collector | `pocc/collector/` | per file | FROZEN |
| OSC configuration | `crontab` | — | ACTIVE |
| CEPSL baseline | `posc/osc/data/cepsl_status.json` | — | ACTIVE |
| Dashboard version | v2.0.0-rc2 | 54 APIs | FROZEN |
| API version | all routes in main.py | per route | FROZEN |
| Feature definition | CWT scalogram via `cwt_generator.py` | — | FROZEN |
| Normalization params | Prior .pt files | per file | FROZEN |
| Inference threshold | Prior distribution parameters | per station | FROZEN |

## Certification

> Every prediction presented in this report was generated using the frozen scientific baseline v2.0.0-rc2-freeze.

**Auditor:** PIMES FOAC Automation
**Date:** 2026-07-16
**Status:** FROZEN
