# Quality Plan — LAWS V2

## 1. Quality Objectives
| Objective | Metric | Target | Owner |
|---|---|---|---|
| System availability | Uptime % | > 99.5% | SRE Lead |
| Prediction accuracy | F1 score | > 0.40 | ML Lead |
| False alarm rate | FAR | < 0.60 | ML Lead |
| Data integrity | CRC32 errors/day | 0 | DevOps |
| Deployment success | First-attempt deploy % | > 90% | DevOps |
| Documentation coverage | API endpoint docs | 100% | Tech Writer |
| Issue resolution | Mean time to resolve (MTTR) | < 4h (P1) | SRE Lead |

## 2. Quality Assurance Procedures

### 2.1 Code Quality
- Linting: ruff on every commit
- Code review: 1 approval required before merge
- Branching: feature → develop → main (git flow)
- No force-push to main

### 2.2 Model Quality
- Model versioning: semantic (laws-v9.5-champion)
- Weight hash: SHA-256 before promotion
- Evaluation gate: blind test metrics must exceed baseline
- Rollback: previous model always available

### 2.3 Data Quality
- Source validation: CRC32 integrity check
- Completeness: > 95% station coverage
- Timeliness: data arrives within expected window
- Consistency: duplicate detection

### 2.4 Documentation Quality
- API: OpenAPI 3.0 spec maintained
- Architecture: Mermaid diagrams updated per release
- SOPs: reviewed quarterly
- ORR: evidence-based, peer-reviewed

## 3. Quality Control Checklist (Per Release)
- [ ] All unit tests pass
- [ ] Linting clean (0 errors)
- [ ] Model hash matches registry
- [ ] API schema valid
- [ ] DB migration tested
- [ ] ORR score > 70
- [ ] Burn-in 48h clean
- [ ] Rollback procedure tested
