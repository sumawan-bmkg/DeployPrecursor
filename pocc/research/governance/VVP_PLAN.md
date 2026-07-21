# V&V Plan — LAWS V2

## 1. Scope
Covers all software, model, and operational components of LAWS V2.

## 2. Verification (Does the system meet specifications?)

### 2.1 Static Verification
| Item | Method | Status |
|---|---|---|
| Code review | Peer review before merge | ACTIVE |
| Linting | flake8/ruff | ACTIVE |
| Type checking | mypy (where applicable) | PLANNED |
| Docstring coverage | Sphinx extraction | ACTIVE |

### 2.2 Unit Testing
| Module | Tests | Coverage Target |
|---|---|---|
| Inference Worker | Prediction pipeline, error handling | > 80% |
| Decision Engine | Gate logic, thresholds | > 90% |
| Station Fusion | Haversine, windowing | > 80% |
| Validation Worker | CRC32, integrity | > 90% |
| API Endpoints | Response schema, error codes | > 70% |

### 2.3 Integration Testing
| Test | Method | Frequency |
|---|---|---|
| Pipeline E2E | Trigger → Prediction → DB | Per deployment |
| API contract | Schema validation | Per deployment |
| DB schema | Migration compatibility | Per release |

### 2.4 System Testing
| Test | Method | Frequency |
|---|---|---|
| Performance | Load test (100 req/s) | Per ORR |
| Stress | 2x normal load | Per ORR |
| Recovery | Kill/restart all services | Per ORR |

## 3. Validation (Does the system meet real-world needs?)

### 3.1 Model Validation
| Level | Method | Acceptance |
|---|---|---|
| Retrospective | Historical blind test (EPEF V1.0) | F1 > 0.40 |
| Prospective | 30-day pilot | Recall > 0.60 |
| Peer Review | GJI review | Acceptance letter |

### 3.2 Operational Validation
| Level | Method | Acceptance |
|---|---|---|
| ORR | 9-checkpoint FRR | Score > 70 |
| Pilot | Shadow + parallel mode | 28 days stable |
| Acceptance | BMKG test (30 items) | All PASS |

### 3.3 Scientific Validation
| Level | Method | Acceptance |
|---|---|---|
| Calibration | Reliability diagram | Slope in [0.8, 1.2] |
| Discrimination | AUC-ROC | > 0.70 |
| Lead time | Distribution analysis | Median > 24h |

## 4. Traceability
All V&V activities trace to requirements via [traceability_matrix.md](../extensions/traceability_matrix.md).
