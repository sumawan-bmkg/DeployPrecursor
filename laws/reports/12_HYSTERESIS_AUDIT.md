# LAWS Phase 5 — Hysteresis Audit (Anti-Flickering)

**Generated:** 2026-06-29 14:19:13
**Station:** ALR, 30 sequential samples
**Method:** Hold ALERT for 10 steps, REVIEW for 5 steps
**Threshold p95:** 9.0914

## Status Transition Comparison

| Metric | Original | Hysteresis |
|--------|----------|------------|
| Transitions | 12 | 9 |
| Flicker rate | 40.0% | 30.0% |
| Reduction | - | 25.0% |

## Timeline

| Day | LAI | Original | Hysteresis |
|-----|-----|----------|------------|
| 20251001 | 1.649 | QUIET | QUIET |
| 20251002 | 2.515 | QUIET | QUIET |
| 20251003 | 1.508 | QUIET | QUIET |
| 20251004 | 1.480 | QUIET | QUIET |
| 20251005 | 0.731 | QUIET | QUIET |
| 20251006 | 4.792 | MONITOR | MONITOR |
| 20251007 | 1.372 | QUIET | QUIET |
| 20251008 | 1.829 | QUIET | QUIET |
| 20251009 | 4.815 | MONITOR | MONITOR |
| 20251010 | 2.148 | QUIET | QUIET |
| 20251011 | 1.376 | QUIET | QUIET |
| 20251012 | 5.594 | MONITOR | MONITOR |
| 20251013 | 1.997 | QUIET | QUIET |
| 20251014 | 2.420 | QUIET | QUIET |
| 20251015 | 1.114 | QUIET | QUIET |
| 20251016 | 9.100 | REVIEW | REVIEW |
| 20251017 | 1.706 | QUIET | REVIEW |
| 20251018 | 1.964 | QUIET | REVIEW |
| 20251019 | 2.155 | QUIET | REVIEW |
| 20251020 | 0.986 | QUIET | REVIEW |
| 20251021 | 1.030 | QUIET | REVIEW |
| 20251022 | 9.134 | REVIEW | REVIEW |
| 20251023 | 2.715 | QUIET | QUIET |
| 20251024 | 1.122 | QUIET | QUIET |
| 20251025 | 0.928 | QUIET | QUIET |
| 20251026 | 9.134 | REVIEW | REVIEW |
| 20251027 | 0.637 | QUIET | REVIEW |
| 20251028 | 1.382 | QUIET | REVIEW |
| 20251029 | 1.515 | QUIET | REVIEW |
| 20251030 | 1.676 | QUIET | REVIEW |

## Impact on Magnitude Readout

| Day | Actual Mag | Est Mag (when active) | Status |
|-----|------------|----------------------|--------|
| 20251001 | 5.44 | - | QUIET |
| 20251002 | 5.44 | - | QUIET |
| 20251003 | 5.44 | - | QUIET |
| 20251004 | 5.44 | - | QUIET |
| 20251005 | 5.44 | - | QUIET |
| 20251006 | 6.54 | - | MONITOR |
| 20251007 | 6.54 | - | QUIET |
| 20251008 | 6.54 | - | QUIET |
| 20251009 | 6.54 | - | MONITOR |
| 20251010 | 6.54 | - | QUIET |
| 20251011 | 6.54 | - | QUIET |
| 20251012 | 6.54 | - | MONITOR |
| 20251013 | 6.54 | - | QUIET |
| 20251014 | 5.58 | - | QUIET |
| 20251015 | 5.58 | - | QUIET |
| 20251016 | 6.19 | 6.14 | REVIEW |
| 20251017 | 6.19 | 5.59 | REVIEW |
| 20251018 | 6.53 | 5.43 | REVIEW |
| 20251019 | 6.53 | 5.60 | REVIEW |
| 20251020 | 6.53 | 5.70 | REVIEW |
| 20251021 | 6.53 | 5.88 | REVIEW |
| 20251022 | 6.53 | 6.16 | REVIEW |
| 20251023 | 6.53 | - | QUIET |
| 20251024 | 6.53 | - | QUIET |
| 20251025 | 6.53 | - | QUIET |
| 20251026 | 5.97 | 6.18 | REVIEW |
| 20251027 | 5.97 | 5.80 | REVIEW |
| 20251028 | 5.97 | 5.94 | REVIEW |
| 20251029 | 5.97 | 5.87 | REVIEW |
| 20251030 | 5.97 | 5.74 | REVIEW |

## Conclusions
1. Hysteresis reduced flicker from 12 (40.0%) to 9 (30.0%) transitions.
2. ALERT hold ensures operator sees sustained warnings, not flickering.
3. Magnitude readout activates only on REVIEW/ALERT — reduces spurious estimates.
4. Recommended for production deployment.