# PIMES Traceability Matrix

**Version:** v2.0.0-rc2-freeze
**Generated:** 2026-07-16

| Requirement | Module | Evidence | Certificate | Owner |
|-------------|--------|----------|-------------|-------|
| Real-time ULF data collection | Collector | OSC hourly snapshots | SOQ | Ops |
| Data validation & integrity | Collector + RDMC | RDMC station signatures (28) | RDMC | Sci |
| CWT preprocessing | RuntimeKernel | PSEP dual execution | PSEP | Eng |
| Tensor generation | RuntimeKernel | Golden dataset tensors | PSEP | Eng |
| Bayesian inference | RuntimeKernel | Inference output | PSEP | Sci |
| Prior distribution | Laws | prior_*.pt (21 stations) | PSEP | Sci |
| Dashboard monitoring | BOCC | 29 pages, 54 APIs | FOAC | Ops |
| Operational stability | OSC | Hourly snapshots | OSC | Ops |
| Integrity verification | CEPSL | SHA256 chain | CEPSL | Sci |
| Scientific equivalence | PSEP | Dual execution results | PSEP | Sci |
| Scientific qualification | CSQ + SOQ | CSQ/SOQ scores | CSQ | Sci |
| Operational qualification | OSRV | OSRV reports (10) | OSRV | Ops |
| Evidence storage | SEOS | 10 evidence files | SEOS | Ops |
| Accreditation | SOAP | SOAP qualification | SOAP | Review |
| Deployment safety | PDM | SHA256 + auto-rollback | FOAC | Eng |
| Configuration freeze | PDM | Production freeze manifest | FOAC | Eng |
| Rollback capability | PDM | Backup + restore | FOAC | Eng |
| Audit trail | Governance | State machine | Governance | Review |
| Release engineering | RC2 | Transition package (9 docs) | FOAC | Eng |
| Risk management | RC2 | Risk register (18 items) | RC2 | Review |
| Reproducibility | — | Reproducibility book | FOAC | Sci |
| Blind test protocol | — | Runbook (10 steps) | FOAC | Sci |
| Publication readiness | — | Publication package | — | Sci |
| Data acquisition | BMKG | Data package spec | WFDP | PM |

## Coverage Summary

| Category | Requirements | Evidence | Coverage |
|----------|-------------|----------|----------|
| Data Collection | 2 | OSC + RDMC | 100% |
| Processing | 3 | PSEP + golden | 100% |
| Dashboard | 2 | FOAC | 100% |
| Scientific | 5 | CSQ/SOQ/OSRV/SEOS | 100% |
| Operational | 5 | OSC/CEPSL/FOAC | 100% |
| Deployment | 3 | PDM + FOAC | 100% |
| Publication | 3 | Pending blind test | 75% |
| **Total** | **23** | — | **96%** |
