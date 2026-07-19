# Project Freeze Policy

**Version:** v2.0.0-rc2-freeze
**Effective:** 2026-07-16 (freeze tag)
**Until:** `v2.0.0-rc2-final` (release tag)

## Allowed Changes
- ✅ Documentation (README, runbook, handbook, reports)
- ✅ Daily scientific snapshots
- ✅ Dashboard text / labels / cosmetic fixes
- ✅ Operational monitoring (new health checks on existing metrics)
- ✅ Bug fixes (null pointer, timeout, rendering errors only)
- ✅ Security patches (dependency CVEs)
- ✅ Operational recovery (restart procedures)

## Forbidden Changes
- ❌ Model retraining or fine-tuning
- ❌ Threshold adjustment (inference, confidence, classification)
- ❌ Feature engineering (new inputs, new transforms)
- ❌ Preprocessing modification (CWT parameters, normalization)
- ❌ Graph topology changes (station graph, adjacency)
- ❌ Checkpoint replacement (prior models, RDMC signatures)
- ❌ Scientific parameter modification (sampling rate, channels)
- ❌ New API endpoints (unless critical bug fix)
- ❌ New dashboard pages (unless critical operational need)
- ❌ New framework, validator, or qualification module

## Review Process
All changes must pass:
1. UUID generation
2. SHA256 before/after logging
3. Reason documented in governance log
4. Rollback plan verified
5. Approval from project lead

## Enforcement
- `v2.0.0-rc2-freeze` tag is immutable
- All changes go through `hotfix` branch (for bug fixes)
- Scientific changes go through `research-next` branch (separate, non-production)
- Paper analysis goes through `paper-gji` branch
- `main` branch only receives validated hotfixes

## Duration
This policy is effective from `blindtest-start` through `v2.0.0-rc2-final`.
