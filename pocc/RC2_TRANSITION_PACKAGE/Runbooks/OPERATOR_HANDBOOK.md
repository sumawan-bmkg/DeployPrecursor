# WP6 — Operator Handbook

**Generated:** 2026-07-16

## Daily Operations

### Morning Check
```bash
python deploy.py status
```
Verify: System HEALTHY, Collector RUNNING, Pages 10/10.

### If anything is wrong
```bash
python deploy.py doctor
```
Runs 12-point health check with pass/fail per component.

## Deployment

```bash
python deploy.py
```
Runs full deploy pipeline (backup → upload → verify → restart → health → report).

## Monitoring

```bash
python deploy.py watch
```
Live dashboard in terminal (refreshes every 5 seconds).

## Emergency Rollback

```bash
python deploy.py emergency
```
Stops current operation, restores from backup, restarts, runs health check.

## Campaign Status

```bash
python deploy.py campaign
```
Shows: campaign day, snapshots, CEPSL baseline, shadow readiness.

## Shadow / RC Readiness

```bash
python deploy.py shadow
```
Shows: data days, health, OSC baseline, CEPSL, CSQ, recommendation.

```bash
python deploy.py rc
```
Shows: burn-in, PSEP, OSC, shadow decision, recommendation.

## Audit

```bash
python deploy.py audit
```
Full system audit across all 10 API endpoints and 10 pages.

## Release

```bash
python deploy.py release
```
Creates release package: manifest, SHA256, certificate.

## Maintenance Mode

```bash
python deploy.py maintenance on
python deploy.py maintenance off
```
Toggles dashboard banner — API stays alive, collector keeps running.

## Troubleshooting

| Symptom | Command | Fix |
|---------|---------|-----|
| Server unreachable | `ping 10.20.229.43` | Check network |
| Dashboard blank | `python deploy.py restart` | Restart backend |
| Collector stopped | `python deploy.py emergency` | Full restart + rollback |
| CEPSL shows COMPROMISED | Normal during changes | Will reset on next OSC cycle |
| Predictions missing | Check `/api/health-model` | Verify inference pipeline |

## Escalation

1. Try `python deploy.py doctor` first
2. If unrecoverable: `python deploy.py emergency`
3. If server down: contact infrastructure team
4. If data issues: check `/waveform` page for coverage status
