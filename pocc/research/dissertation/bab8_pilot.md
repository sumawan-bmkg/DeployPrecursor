# Bab VIII: Pilot Operation

## 8.1 Shadow Mode (Hari 1-14)
Sistem berjalan paralel dengan operasi BMKG eksisting. Prediksi dihasilkan tetapi tidak didiseminasikan sebagai peringatan.

Monitoring: daily comparison report antara prediksi LAWS V2 dengan catalog gempa BMKG.

## 8.2 Parallel Evaluation (Hari 15-28)
Prediksi dibagikan kepada operator sebagai advisory. Operator mencatat penilaian kualitatif terhadap kualitas prediksi.

## 8.3 Ground Truth Comparison
Setiap prediksi diverifikasi terhadap:
- BMKG earthquake catalog (spatial + temporal matching)
- Operator log (kualitatif)
- Lead time aktual

## 8.4 Operational Stability
- Uptime: target > 99.5%
- Pipeline completion: semua siklus selesai tepat waktu
- Error rate: < 1% per hari
- Restart count: < 1 per 72 jam

## 8.5 Escalation Procedures
| Level | Trigger | Response |
|---|---|---|
| P0 | System down | Restart + root cause analysis |
| P1 | Degradation | Operator notification within 1h |
| P2 | Anomaly | Weekly review |

## 8.6 Pilot Closure Criteria
- 28 hari data operasional terkumpul
- Semua metrik memenuhi threshold
- Operator confidence score > 3.5/5
- Rekomendasi: GO untuk full operational handover
