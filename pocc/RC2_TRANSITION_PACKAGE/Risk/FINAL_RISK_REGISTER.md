# WP8 — Final Risk Register

**Generated:** 2026-07-16

## Risk Categories

### Technical Risks

| # | Risk | Probability | Impact | Mitigation | Owner |
|---|------|-------------|--------|------------|-------|
| T1 | Server unreachable | LOW | CRITICAL | PDM auto-retry + network monitoring | Ops |
| T2 | Disk full (423 GB free) | LOW | HIGH | Monitor `/opt/pimes/data/` size, alert at 90% | Ops |
| T3 | Blue-green restart fails | LOW | HIGH | Fallback to direct restart, rollback on health failure | PDM |
| T4 | SHA256 checksum mismatch | LOW | MEDIUM | Auto-block deploy, report mismatch | PDM |
| T5 | Collector process dies | MEDIUM | HIGH | Systemd restart policy, `deploy restart` as fallback | Ops |

### Scientific Risks

| # | Risk | Probability | Impact | Mitigation | Owner |
|---|------|-------------|--------|------------|-------|
| S1 | Waveform 2025-2026 still unavailable | HIGH | CRITICAL | Request BMKG data — current blocker | PM |
| S2 | `.lem` parser incorrect timestamps | MEDIUM | HIGH | LFCP characterization complete, binary validated | Eng |
| S3 | Model drift on new data | MEDIUM | HIGH | OSC hourly snapshots detect drift early | Sci |
| S4 | CEPSL baseline COMPROMISED permanently | LOW | HIGH | Baseline lock with SHA256, re-anchor on new cycle | Sci |

### Operational Risks

| # | Risk | Probability | Impact | Mitigation | Owner |
|---|------|-------------|--------|------------|-------|
| O1 | Operator unfamiliar with PDM | MEDIUM | MEDIUM | Handbook provided (WP6) + wizard mode | Ops |
| O2 | Wrong deploy command | LOW | LOW | Risk gate blocks dangerous changes | PDM |
| O3 | Rollback backup not available | LOW | CRITICAL | Every backup before deploy | PDM |
| O4 | Dashboard stale data | LOW | MEDIUM | Auto-refresh every 30s, health check API | Dashboard |

### Data Risks

| # | Risk | Probability | Impact | Mitigation | Owner |
|---|------|-------------|--------|------------|-------|
| D1 | BMKG data format mismatch | MEDIUM | HIGH | Acquisition spec defines accepted formats | PM |
| D2 | Incomplete station coverage | MEDIUM | MEDIUM | 21 stations with priors is sufficient baseline | Sci |
| D3 | Low SNR in waveform | MEDIUM | MEDIUM | Confidence score threshold in inference | Sci |
| D4 | Timezone errors in catalog | LOW | HIGH | `merge2026.csv` is UTC-consistent | Audit |

### Security Risks

| # | Risk | Probability | Impact | Mitigation | Owner |
|---|------|-------------|--------|------------|-------|
| C1 | Unauthorized server access | LOW | CRITICAL | SSH key auth + internal network | IT |
| C2 | Data integrity violation | LOW | HIGH | CEPSL SHA256 chain detects any change | Sci |
| C3 | Credential exposure | LOW | CRITICAL | Credentials in paramiko (access-controlled env) | IT |

## Risk Summary

| Severity | Count | Action |
|----------|-------|--------|
| CRITICAL | 4 | Requires immediate mitigation |
| HIGH | 9 | Requires active monitoring |
| MEDIUM | 6 | Tracked, lower priority |
| LOW | 3 | Acceptable risk |

## Top 3 Blocking Risks

1. **S1**: Waveform 2025-2026 unavailable — **blocks blind test entirely**
2. **T5**: Collector process death — requires monitoring
3. **D1**: BMKG data format mismatch — mitigated by acquisition package
