# Pilot Operation Design — LAWS V2

## 1. Operational Mode

### 1.1 Shadow Mode (First 14 Days)
- Backend runs in parallel with existing BMKG operations
- Predictions generated but NOT disseminated as warnings
- All outputs logged for offline evaluation
- No operational decisions made based on LAWS V2 predictions

### 1.2 Parallel Evaluation (Next 14 Days)
- Predictions shared with duty operator as advisory only
- Operator logs assessment of prediction quality
- Ground truth collected from BMKG catalog
- Weekly review meeting

## 2. Evaluation Timeline
| Day | Activity | Deliverable |
|---|---|---|
| 1-14 | Shadow mode | Daily comparison report |
| 15 | Transition review | Shadow summary |
| 16-28 | Parallel operation | Operator feedback |
| 29-30 | Final review | Pilot closure report |

## 3. Daily Assessment
- Morning: check all predictions from past 24h
- Compare with BMKG catalog
- Log: Hit / Miss / False Alarm / Correct Null
- Compute cumulative metrics

## 4. Go/No-Go Criteria for Full Operational Status
| Criterion | Required | Measurement |
|---|---|---|
| Detection Rate | > 60% | Cumulative 28 days |
| FAR | < 40% | Cumulative 28 days |
| Lead Time | > 24h median | Cumulative 28 days |
| Uptime | > 99.5% | systemd logs |
| Operator Confidence | > 3.5/5 | Survey at day 28 |

## 5. Escalation to BMKG Management
- Weekly executive summary
- Metrics dashboard
- Risk assessment
- Recommendation for full operational release
