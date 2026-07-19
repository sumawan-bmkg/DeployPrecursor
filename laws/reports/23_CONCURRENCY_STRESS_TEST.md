# LAWS Phase 9 — Concurrency & Stress Test Report

**Generated:** 2026-06-29 16:17:33
**Mode:** DIRECT PIPELINE
**Simulated stations:** 22  |  **Waves:** 20  |  **Total inferences:** 440

## Test Configuration

| Parameter | Value |
|-----------|-------|
| Stations per wave | 22 |
| Waves | 20 |
| Total inferences | 440 |
| Station codes | ALR, AMB, CLP, GTO, KPY... (22 total) |
| Cosmic Kp range | 1.0 – 7.0 (includes storm conditions) |
| Cosmic Dst range | -60 – -10 nT |
| Test mode | Direct pipeline

## Performance Metrics

| Metric | Value | Target | Pass? |
|--------|-------|--------|-------|
| Mean latency | 99.56 ms | — | — |
| p50 latency | 159.76 ms | — | — |
| p95 latency | 198.66 ms | <300 ms | ✅ |
| p99 latency | 242.77 ms | — | — |
| Min latency | 6.59 ms | — | — |
| Max latency | 300.46 ms | — | — |
| Throughput (RPS) | 221 req/s | — | — |
| Memory before | 33.7 MB | — | — |
| Memory after | 1454.6 MB | — | — |
| Memory drift | +1420.9 MB | <20 MB | ❌ |

## Latency Distribution

```
  p50: 159.8 ms
  p95: 198.7 ms
  p99: 242.8 ms
  Mean: 99.6 ms
  Std:  85.52 ms
```

## Memory Stability

- **Pre-test:** 33.7 MB
- **Post-test (440 inferences):** 1454.6 MB
- **Drift:** +1420.9 MB
- **Verdict:** ⚠️ Memory growth detected — review required

## Conclusion

**⚠️ Review required before operational deployment.**
- Memory growth detected — investigate ONNX session handling.
