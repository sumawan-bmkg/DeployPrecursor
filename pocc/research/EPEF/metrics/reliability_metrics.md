# Reliability Metrics — EPEF V1.0

## 1. System Availability
\[
A = \frac{T_{\text{up}}}{T_{\text{total}}} \times 100\%
\]

| Component | Target SLA | Measurement |
|---|---|---|
| Backend API | 99.5% | /api/health response |
| Dashboard | 99.0% | systemd status |
| Collector | 99.5% | systemd status + cycle completion |
| Predictor | 99.9% | /api/predictor status |
| PostgreSQL | 99.9% | pg_isready |
| Scheduler | 99.5% | PID + cycle check |

## 2. MTBF & MTTR
\[
MTBF = \frac{T_{\text{total}} - T_{\text{down}}}{N_{\text{failures}}}
\]
\[
MTTR = \frac{T_{\text{down}}}{N_{\text{failures}}}
\]

## 3. Error Budget
Monthly error budget = total permitted downtime:
- 99.5% SLA → 216 minutes/month
- 99.9% SLA → 43 minutes/month

## 4. Failure Modes
| Mode | Impact | MTBF Target |
|---|---|---|
| Service crash | High | > 720h |
| DB connection loss | Critical | > 720h |
| Prediction failure | Critical | > 168h |
| Data stall | Medium | > 168h |
