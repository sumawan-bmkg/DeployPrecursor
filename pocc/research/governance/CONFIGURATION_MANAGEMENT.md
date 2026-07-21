# Configuration Management — LAWS V2

## 1. Configuration Items (CIs)

| CI | Type | Location | Owner |
|---|---|---|---|
| Source code | Software | Git repo (GitHub) | DevOps Lead |
| Model weights | Data | `/opt/pimes/laws/predict_cli.py` | MLOps Lead |
| PostgreSQL schema | Database | `/opt/pimes/pocc/schema.sql` | DB Architect |
| systemd units | Config | `/etc/systemd/system/pocc-*.service` | SRE Lead |
| NGINX config | Config | `/etc/nginx/sites-available/pocc` | SRE Lead |
| Python venv | Runtime | `/opt/pimes/laws/runtime/.venv/` | DevOps Lead |
| Dashboard static | Asset | `/opt/pimes/pocc/backend/static/` | Frontend Lead |
| ORR docs | Governance | `docs/ORR_*.md` | Project Lead |
| Research docs | Knowledge | `research/` | Research Lead |

## 2. Versioning Scheme
```
Major.Minor.Patch[-qualifier]

Example: v0.2.0-rc2
  Major = breaking schema change
  Minor = new feature or significant fix
  Patch = bug fix
  qualifier = dev | rc1 | rc2 | stable
```

## 3. Baseline Management
| Baseline | Commit | Date | Status |
|---|---|---|---|
| ORR Baseline | `d22f11b` | 20 Jul 2026 | FROZEN |
| Extensions | `4bf91e1` | 21 Jul 2026 | FROZEN |
| Governance | Current | 21 Jul 2026 | IN PROGRESS |

## 4. Configuration Control Board (CCB)
- **Members**: System Architect (chair), SRE Lead, ML Lead, BMKG Rep
- **Scope**: Any change to CI in FROZEN state requires CCB approval
- **Process**: RFC → CCB Review → Approve/Reject → Implement → Verify
