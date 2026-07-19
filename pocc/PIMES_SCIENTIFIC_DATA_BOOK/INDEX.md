# PIMES Scientific Data Book

**Version:** v2.0.0-rc2-freeze
**Tag:** `v2.0.0-rc2-freeze`
**Date:** 2026-07-16

---

## Table of Contents

| # | Section | Status |
|---|---------|--------|
| 01 | [Project Overview](01_Project_Overview/PROJECT_OVERVIEW.md) | ✅ |
| 02 | System Architecture | 📄 |
| 03 | Data Pipeline | 📄 |
| 04 | Model | 📄 |
| 05 | Runtime | 📄 |
| 06 | [Deployment](https://github.com/sumawan-bmkg/DeployPrecursor/blob/main/RC2_TRANSITION_PACKAGE/Deployment/DEPLOYMENT_HARDENING_REPORT.md) | ✅ |
| 07 | [Dashboard](https://github.com/sumawan-bmkg/DeployPrecursor/blob/main/RC2_TRANSITION_PACKAGE/Dashboard/DASHBOARD_FINAL_REVIEW.md) | ✅ |
| 08 | Collector | 📄 |
| 09 | Operational Campaign | 📄 |
| 10 | [WFDP](C:\Users\Admin\.gemini\antigravity\brain\d99cc142-5304-4d6e-9a68-187d102e1f31\WAVEFORM_DISCOVERY_REPORT.md) | ✅ |
| 11 | [LFCP](C:\Users\Admin\.gemini\antigravity\brain\d99cc142-5304-4d6e-9a68-187d102e1f31\LEM_FORMAT_CHARACTERIZATION.md) | ✅ |
| 12 | [FOAC](C:\Users\Admin\.gemini\antigravity\brain\d99cc142-5304-4d6e-9a68-187d102e1f31\FINAL_ACCEPTANCE_CERTIFICATE.md) | ✅ |
| 13 | [RC2 Transition Package](https://github.com/sumawan-bmkg/DeployPrecursor/blob/main/RC2_TRANSITION_PACKAGE/) | ✅ |
| 14 | Blind Test Methodology | 📄 |
| 15 | ERB Assessment | 📄 |
| 16 | [Risk Register](https://github.com/sumawan-bmkg/DeployPrecursor/blob/main/RC2_TRANSITION_PACKAGE/Risk/FINAL_RISK_REGISTER.md) | ✅ |
| 17 | [Final Certificate](https://github.com/sumawan-bmkg/DeployPrecursor/blob/main/RC2_TRANSITION_PACKAGE/Certificates/EXECUTIVE_READINESS_CERTIFICATE.md) | ✅ |
| 18 | Publication Appendix | 📄 |

**Legend:** ✅ Complete | 📄 Template (fill when data available)

---

## Quick Links

| Resource | Location |
|----------|----------|
| Deploy Manager | `pocc/deploy.py` |
| Dashboard | `pocc/backend/main.py` (port 8500) |
| PDM Commands | `python deploy.py [status|doctor|deploy|rollback|...]` |
| Operator Handbook | `RC2_TRANSITION_PACKAGE/Runbooks/OPERATOR_HANDBOOK.md` |
| Blind Test SOP | `RC2_TRANSITION_PACKAGE/Runbooks/BLIND_TEST_RUNBOOK.md` |
| BMKG Data Spec | `RC2_TRANSITION_PACKAGE/BMKG/BMKG_DATA_PACKAGE_SPECIFICATION.md` |
| Evidence Chain | OSC hourly + CEPSL SHA256 chain |
| System Health | `http://10.20.229.43:8500` |

---

## Contact

**System Owner:** BMKG
**Technical Lead:** PIMES Engineering Team
**Evidence Review Board:** Established
