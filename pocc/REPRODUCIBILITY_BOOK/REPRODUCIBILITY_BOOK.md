# Reproducibility Book

**Version:** v2.0.0-rc2-freeze
**Generated:** 2026-07-16

## Environment

| Component | Value |
|-----------|-------|
| OS | Ubuntu (Linux) |
| Python | 3.12 (runtime venv) |
| Runtime venv | `/opt/pimes/laws/runtime/.venv/` |
| Server | 10.20.229.43 |
| Git tag | v2.0.0-rc2-freeze |

## Git Snapshot

```
Commit:   dddbd0e → 66bead3
Tag:      v2.0.0-rc2-freeze (annotated)
Branch:   main
Date:     2026-07-16
```

## Critical File Hashes (SHA256-256, truncated)

| File | Hash | Size |
|------|------|------|
| `backend/main.py` | `2340b3d4333073bb` | 34,234 B |
| `deploy.py` | `a083302fc70b839d` | 24,107 B |
| `templates/base.html` | `da0ea23e4e02f996` | 4,135 B |
| `templates/governance.html` | `4cb5a51a47923515` | 2,972 B |
| `templates/collector.html` | `16fabc4ee1536b7c` | 3,718 B |
| `templates/reports.html` | `ef84cc4b2aa7f43f` | 2,662 B |
| `templates/deployment.html` | `07562765285526eb` | 4,609 B |
| `templates/data_readiness.html` | `5a8ae8ca3c07d365` | 5,318 B |
| `templates/waveform.html` | `97421166ad1c65dd` | 5,538 B |

## Full Manifest

Saved at: `manifests/PRODUCTION_FREEZE_20260716.json`

## How to Reproduce

```bash
# 1. Clone at the frozen tag
git clone --branch v2.0.0-rc2-freeze https://github.com/sumawan-bmkg/DeployPrecursor

# 2. Install Python 3.12
# 3. Create venv and install requirements (requirements.txt)
# 4. Deploy
python deploy.py deploy

# 5. Verify
python deploy.py doctor
```

## Known Limitations

1. Waveform data 2025-2026 not available (requires BMKG external transfer)
2. Prior models trained on historical ULF data — not validated against 2026 data
3. Burn-in incomplete (2/24 cycles — process died before completion)
4. Golden dataset limited to 3 stations (ALR, LWA, PLU)
