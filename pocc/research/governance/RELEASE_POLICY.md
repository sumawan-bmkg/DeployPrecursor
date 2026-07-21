# Release Policy — LAWS V2

## 1. Release Types

| Type | Scope | Approval | Testing |
|---|---|---|---|
| Hotfix | Critical bug fix | System Architect | Unit + integration |
| Patch | Non-critical bug fix | DevOps Lead | Unit test |
| Minor | New feature (backward-compatible) | CCB | Full regression |
| Major | Breaking change | CCB + BMKG approval | ORR required |

## 2. Release Gates

### 2.1 Pre-Release Checklist
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Linting clean
- [ ] Model hash verified (if model change)
- [ ] DB migration tested (if schema change)
- [ ] Changelog updated
- [ ] Release notes written
- [ ] CCB approval (for minor/major)

### 2.2 Deployment Gates
- [ ] Staging deployment successful
- [ ] Smoke test passed
- [ ] No P0/P1 issues in staging
- [ ] Rollback procedure tested
- [ ] Monitoring alerts configured

### 2.3 Post-Release Verification
- [ ] Production health check (API, dashboard)
- [ ] Pipeline running (scheduler, collector)
- [ ] No new errors in log (24h)
- [ ] Database performance normal
- [ ] User feedback collected (72h)

## 3. Versioning
Following semantic versioning:
```
v{MAJOR}.{MINOR}.{PATCH}[-{qualifier}]
```
Examples:
- `v0.2.0-rc2` — current production
- `v0.2.1` — first bug fix release
- `v0.3.0` — first feature release
- `v1.0.0` — first stable production release (after pilot)
