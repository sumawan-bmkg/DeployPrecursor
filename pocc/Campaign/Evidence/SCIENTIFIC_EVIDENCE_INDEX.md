# Scientific Evidence Index

**Purpose:** One-page registry of all evidence. Every file has UUID, SHA256, date, and level.
**Root:** `Campaign/Evidence/`

---

| UUID | File | SHA256 | Date | Level | MSCM Claim | Status |
|------|------|--------|------|-------|------------|--------|
| EV-001 | OSC daily log (Day 1) | ❓ | 2026-07-16 | E1 | C03 | 🔄 |
| EV-002 | CEPSL snapshot chain | ❓ | Ongoing | E2 | C13 | 🔄 |
| EV-023 | FOAC acceptance certificate | ❓ | 2026-07-15 | E4 | C09 | ✅ |
| EV-024 | Production freeze manifest | `a083302f...` | 2026-07-16 | E3 | C12 | ✅ |
| EV-035 | Reproducibility book | ❓ | 2026-07-16 | E2 | C04 | ⏳ |
| EV-036 | SBTP v2.0 protocol | ❓ | 2026-07-16 | E3 | C11 | ✅ |
| EV-110 | False alarm protocol | ❓ | 2026-07-16 | E2 | C07 | ⏳ |
| EV-115 | EEJ classification report | ❓ | 2026-07-16 | E2 | C08 | ✅ |
| EV-118 | Geomagnetic disturbance dataset | ❓ | 2026-07-16 | E2 | C17 | ✅ |
| EV-120 | Physics validation protocol | ❓ | 2026-07-16 | E2 | C06 | ⏳ |
| EV-107 | Explainability protocol | ❓ | 2026-07-16 | E2 | C05 | ⏳ |
| EV-TBD-01 | Blind test prediction registry | ❓ | Future | E3 | C01-C02, C10, C14-C15, C18 | ⏳ |
| EV-TBD-02 | Evaluation metrics report | ❓ | Future | E4 | C01-C02 | ⏳ |
| EV-TBD-03 | Null model comparison | ❓ | Future | E4 | C02 | ⏳ |
| EV-TBD-04 | Physics validation results | ❓ | Future | E3 | C06, C16 | ⏳ |
| EV-TBD-05 | Publication manuscript | ❓ | Future | E5 | All | ⏳ |

---

## Legend

| Level | Definition |
|-------|-----------|
| E0 | Raw observation (collector output) |
| E1 | Verified observation (checksum valid, timestamp valid) |
| E2 | Qualified dataset (passed Data Qualification Gate) |
| E3 | Scientific evidence (used for statistical analysis) |
| E4 | Published evidence (figure/table in paper) |
| E5 | Independent reproduction (reproduced by external evaluator) |
