# Publication Traceability Matrix

**Purpose:** Every figure and table in the paper traces to a specific evidence UUID, prediction IDs, dataset, and collector snapshot.

---

## Figures

| Figure | Description | Evidence UUID | Prediction IDs | Raw Dataset | Collector Snapshot | MSCM Claim |
|--------|-------------|---------------|----------------|-------------|--------------------|------------|
| Fig 1 | System architecture | EV-023 | — | — | — | C09 |
| Fig 2 | Data pipeline | EV-036 | — | — | — | C11 |
| Fig 3 | Dashboard screenshot | EV-001 | — | — | OSC Day N | C03 |
| Fig 4 | Station map + EEJ zones | EV-115 | — | — | — | C08 |
| Fig 5 | ROC curve | EV-TBD-02 | All TPs/FPs | merge2026.csv | OSC Day N | C01 |
| Fig 6 | PR curve | EV-TBD-02 | All TPs/FPs | merge2026.csv | OSC Day N | C01 |
| Fig 7 | Reliability diagram | EV-TBD-02 | All TPs/FPs | merge2026.csv | — | C14 |
| Fig 8 | Confusion matrix | EV-TBD-02 | All TPs/FPs | merge2026.csv | — | C01 |
| Fig 9 | Lead time distribution | EV-TBD-02 | TP predictions | merge2026.csv | — | C18 |
| Fig 10 | Station attribution heatmap | EV-TBD-03 | Per-station TPs/FPs | merge2026.csv | — | C10 |
| Fig 11 | Physics validation panel | EV-TBD-04 | TP predictions | merge2026.csv + cosmic | — | C06, C16 |
| Fig 12 | FP characterization | EV-TBD-02 | FP predictions | merge2026.csv + cosmic | — | C07 |
| Fig 13 | Blind test timeline | EV-TBD-01 | All predictions | — | OSC Day N | C11 |
| Fig 14 | Null model comparison | EV-TBD-03 | All (all models) | merge2026.csv | — | C02 |

## Tables

| Table | Description | Evidence UUID | MSCM Claim |
|-------|-------------|---------------|------------|
| Table 1 | Primary results (all models) | EV-TBD-03 | C01, C02, C14 |
| Table 2 | Per-station metrics (21 stations) | EV-TBD-02 | C10 |
| Table 3 | Stratified results (Dst, time, EEJ, mag) | EV-TBD-02 | C07, C08, C16 |
| Table 4 | Sensitivity analysis | EV-TBD-02 | C15 |
| Table 5 | Calibration metrics (ECE/MCE per model) | EV-TBD-02 | C14 |
| Table 6 | Ablation results | EV-TBD-03 | C02 |
| Table 7 | Deployment metrics | EV-024 | C12 |
| Table 8 | Evidence atlas snapshot | EV-023 | C09 |

## Supplementary

| Item | Description | Evidence UUID |
|------|-------------|---------------|
| Fig S1 | Reproducibility (diff test) | EV-035 |
| Fig S2 | Example anomaly time series | EV-TBD-04 |
| Fig S3 | EEJ station map | EV-115 |
| Data availability | Code + environment + SHA256 | EV-035, EV-024 |

---

## Data Flow

```
collector_worker_YYYYMMDD_HHMMSS.log      (raw observation, E0)
    → SHA256 verification                  (verified, E1)
    → file.lem → CWT → tensor.npy          (qualified, E2)
    → model inference → prediction.csv     (scientific, E3)
    → registry → matching → metrics.json   (scientific, E3)
    → figure.png → table.tex              (published, E4)
    → paper-gji repository                (published, E4)
```

The hash chain ensures every figure can be traced back to the raw collector snapshot that produced it.
