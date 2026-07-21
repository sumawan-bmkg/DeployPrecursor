# Traceability Matrix — LAWS V2

## 1. Requirements to Modules

| ID | Requirement | Source | Module | Evidence |
|---|---|---|---|---|
| R01 | Real-time data ingestion | SRS | Discovery Worker | cycle=300s, FTP pull |
| R02 | Data integrity check | SRS | Validation Worker | CRC32 fix deployed |
| R03 | Precursor analysis | SRS | Inference Worker | QG+PC3+CWT ensemble |
| R04 | Prediction output | SRS | LAWSRealPredictor | /api/predictor status=loaded |
| R05 | Decision engine | SRS | Decision Gate | 4-level: N/A/W/W* |
| R06 | Station fusion | SRS | Station Fusion | 500km/2h window |
| R07 | Event management | SRS | EventManager | lifecycle NEW→CLOSED |
| R08 | Warning issuance | SRS | WarningManager | lifecycle ACTIVE→RETRACTED |
| R09 | Dashboard display | SRS | Backend API | /api/overview, /api/predictor |
| R10 | Pipeline tracking | SRS | PipelineRun | DB: pipeline_runs table |
| R11 | Audit trail | SRS | Audit Worker | DB: audit_log table |
| R12 | Evidence generation | SRS | Evidence Worker | Deferred (Stage 3) |
| R13 | Operational monitoring | SRS | systemd | Restart always: 5s |
| R14 | Database persistence | SRS | PostgreSQL 16 | 7 tables, indexes |
| R15 | Failure recovery | SRS | systemd | Auto-restart, logging |

## 2. Tests to Requirements

| ID | Test | Requirement |
|---|---|---|
| T01 | systemctl is-active | R13, R15 |
| T02 | curl /api/health | R09 |
| T03 | curl /api/predictor | R04 |
| T04 | curl /api/overview | R09 |
| T05 | PG query predictions table | R10 |
| T06 | PG query decisions table | R05 |
| T07 | PG query events table | R07 |
| T08 | PG query warnings table | R08 |
| T09 | Check collector.log | R01, R02 |
| T10 | Check CRC32 errors | R02 |

## 3. ORR Findings to Requirements

| Finding | Requirement | Status |
|---|---|---|
| CF-01 (label bug) | R09 | CLOSED |
| CF-02 (CRC32 bug) | R02 | CLOSED |
| CA-03 (systemd) | R13 | OPEN |
| CA-04 (logrotate) | R13 | OPEN |
| ... | ... | ... (18 remaining) |
