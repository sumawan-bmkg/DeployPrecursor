# Research Registry — EPEF V1.0

## Purpose
Central log of all experiments conducted under EPEF evaluation framework. Each experiment tracks: configuration, data, model, commit, seed, metrics.

---

## Experiment Log

### Experiment 001 — Baseline: Random Predictor
| Field | Value |
|---|---|
| **Date** | TBD |
| **Model** | Random uniform noise |
| **Dataset** | BMKG 2022-2023 |
| **Seed** | 42 |
| **Commit** | `ae3084d` |
| **Split** | 60/20/20 |
| **Episodes** | N/A (analytic) |
| **Result** | [TBD — run during blind test] |
| **Notes** | Lower bound for all metrics |

### Experiment 002 — LAWS V2 Blind Test
| Field | Value |
|---|---|
| **Date** | TBD |
| **Model** | LAWSV95Real (frozen) |
| **Dataset** | BMKG 2022-2023 |
| **Seed** | 42 |
| **Commit** | `ae3084d` |
| **Split** | Test set only (no train) |
| **Inference** | Single-pass, no retries |
| **Result** | [TBD] |
| **Notes** | Primary evaluation for GJI paper |

### Experiment 003 — CNN Baseline
| Field | Value |
|---|---|
| **Date** | TBD |
| **Model** | 1D-CNN, 3-layer |
| **Dataset** | BMKG 2015-2023 |
| **Seed** | 42, 43, 44 (3-fold) |
| **Commit** | TBD |
| **Split** | 60/20/20 |
| **Epochs** | max 100 (early stop 10) |
| **Result** | [TBD] |

### Experiment 004 — LSTM Baseline
| Field | Value |
|---|---|
| **Date** | TBD |
| **Model** | 2-layer LSTM, 128 hidden |
| **Dataset** | BMKG 2015-2023 |
| **Seed** | 42, 43, 44 |
| **Commit** | TBD |
| **Split** | 60/20/20 |
| **Epochs** | max 100 |
| **Result** | [TBD] |

... [More entries as experiments are executed]

## Template for New Experiments
```markdown
### Experiment XXX — [Name]
| Field | Value |
|---|---|
| **Date** | [Date] |
| **Model** | [Model name + version] |
| **Dataset** | [Source + period] |
| **Seed** | [Seed values] |
| **Commit** | [Git commit hash] |
| **Split** | [Train/Val/Test ratio] |
| **Epochs** | [Training epochs] |
| **Result** | [Summary metrics] |
| **Notes** | [Key observations] |
```
