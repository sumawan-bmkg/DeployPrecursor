# Risk Register — LAWS V2

## 1. Risk Matrix

| ID | Risk | Likelihood | Impact | Score | Mitigation | Owner |
|---|---|---|---|---|---|---|
| R01 | Model produces systematic false alarms | Medium | High | 12 | Threshold tuning, StormGate | ML Lead |
| R02 | Station data loss (extended outage) | Medium | Medium | 9 | Redundant stations, graceful degradation | SRE Lead |
| R03 | PostgreSQL corruption | Low | Critical | 12 | Hourly backup, WAL archiving | DB Architect |
| R04 | Solar storm contamination | High | Medium | 12 | Kp-based suppression, Dst tagging | ML Lead |
| R05 | Prediction quality degrades over time | Medium | High | 12 | Retraining schedule, monitoring | MLOps Lead |
| R06 | Operator fatigue (too many false alarms) | High | Medium | 12 | Threshold tuning, alert deduplication | SRE Lead |
| R07 | BMKG acceptance delayed | Low | High | 8 | Clear acceptance criteria, staged pilot | Project Lead |
| R08 | Publication rejected | Medium | Medium | 9 | Strong methodology, peer review | Research Lead |
| R09 | Regulatory change (new BMKG requirements) | Low | High | 8 | Modular architecture, adaptable SOPs | Project Lead |
| R10 | Key person dependency | Medium | High | 12 | Documentation, cross-training | Project Lead |

## 2. Risk Score
Score = Likelihood × Impact (1-3 × 1-3 × 1-4)
- **Critical (16+)**: Immediate mitigation required
- **High (10-15)**: Active mitigation, monthly review
- **Medium (5-9)**: Quarterly review
- **Low (1-4)**: Annual review

## 3. Risk Response Log
| Date | Risk | Action | Result | Residual Risk |
|---|---|---|---|---|
| 20 Jul 2026 | R03 | Hourly pg_dump | Active | Low |
| 20 Jul 2026 | R04 | StormGate Kp>4 | Active | Low |
| 21 Jul 2026 | R10 | Documentation (this governance package) | Active | Medium |
