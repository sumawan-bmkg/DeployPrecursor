# WP5 — Dashboard Final Review

**Generated:** 2026-07-16

## Page Inventory (29 pages)

| Page | Route | Status Indicators | Data |
|------|-------|-------------------|------|
| Overview | `/` | System health, collector status | Live API |
| Collector | `/collector` | Collector workers, file counts | Live API |
| Runtime | `/runtime` | Pipeline stages | Live API |
| Scientific | `/scientific` | Scientific metrics | Live API |
| Burn-in | `/burnin` | Burn-in cycles | Static |
| PSEP | `/psep` | PSEP equivalence | Static |
| Release | `/release` | Release status | Live API |
| Executive | `/executive` | Executive summary | Live API |
| Governance | `/governance` | State machine, actions | Live API |
| Reports | `/reports` | Daily reports | Live API |
| Deployments | `/deployment` | Deploy history, timeline | Live API |
| **Data Readiness** | `/data-readiness` | Component readiness | Static JS |
| **Waveform** | `/waveform` | Waveform coverage | Static audit |
| Stations | `/stations` | Station status | Static |
| System | `/system` | System info | Live API |
| Shadow | `/shadow` | Shadow readiness | Live API |
| Audit | `/audit` | Audit trail | Live API |
| Analytics | `/analytics` | Analytics | Live API |
| Artifacts | `/artifacts` | Evidence artifacts | Live API |
| Digital Twin | `/digitaltwin` | Digital twin | Live API |
| Engineering | `/engineering` | Engineering metrics | Live API |
| Scientific Ops | `/scientific-ops` | Scientific operations | Live API |
| Pipeline Runtime | `/pipeline-runtime` | Pipeline real-time | Live API |
| Alert Center | `/alert-center` | Alerts | Live API |
| Evidence Center | `/evidence-center` | Evidence inventory | Live API |
| Release Center | `/release-center` | Release center | Live API |
| Executive Center | `/executive-center` | Executive center | Live API |
| Mission Timeline | `/mission-timeline` | Mission timeline | Live API |
| Blind Test | `/blindtest` | (reserved) | — |

## Status Indicators

The dashboard uses these color-coded status indicators:

| Indicator | Meaning |
|-----------|---------|
| `HEALTHY` (green) | System operating normally |
| `RUNNING` (green) | Component actively processing |
| `COMPROMISED` (yellow) | Baseline hash mismatch (expected during active changes) |
| `MISSING` (red) | Data not available |
| `BLOCKED` (red) | Cannot proceed — data dependency |
| `READY` (green) | Component validated and frozen |
| `PARTIAL` (yellow) | Some but not all requirements met |
| `CONDITIONAL GO` | Ready except for one blocker |

## Key Pages for Operator

1. **`/`** — Check system health every day
2. **`/waveform`** — Check if BMKG data has arrived
3. **`/deployment`** — Check deployment history and rollback status
4. **`/data-readiness`** — See overall data pipeline readiness
5. **`/governance`** — Review governance actions and state machine
