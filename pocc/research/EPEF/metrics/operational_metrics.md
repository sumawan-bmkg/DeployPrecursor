# Operational Metrics — EPEF V1.0

## 1. Collection Completeness
\[
C_{\text{coll}} = \frac{N_{\text{files\_downloaded}}}{N_{\text{files\_expected}}} \times 100\%
\]

## 2. Validation Success Rate
\[
V_{\text{rate}} = \frac{N_{\text{valid}}}{N_{\text{total\_checks}}} \times 100\%
\]

## 3. Pipeline Latency
| Stage | Target | Alarm |
|---|---|---|
| Discovery | < 300s | > 600s |
| Download | < 600s | > 900s |
| Validation | < 60s | > 120s |
| Inference | < 60s | > 120s |
| Total cycle | < 1020s | > 1800s |

## 4. Evidence Completeness
\[
E_{\text{complete}} = \frac{N_{\text{generated}}}{N_{\text{expected\_daily}}} \times 100\%
\]

## 5. Dashboard Availability
- Uptime % (systemd)
- Response latency (p95 < 500ms)
- Error rate (HTTP 5xx < 1%)

## 6. Database Performance
- Active connections < 20
- Query latency p95 < 100ms
- DB size growth < 500MB/month
- Index hit rate > 95%
