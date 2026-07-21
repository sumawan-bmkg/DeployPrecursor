# Benchmark Protocol — EPEF V1.0

## 1. Purpose
Systematic comparison of LAWS V2 against standard deep learning baselines for earthquake precursor detection.

## 2. Competing Models

| Model | Type | Reference | Implementation |
|---|---|---|---|
| **CNN** | 1D Convolutional | Standard | 3-layer 1D-CNN + FC |
| **LSTM** | Recurrent | Hochreiter 1997 | 2-layer LSTM, 128 hidden |
| **Transformer** | Attention | Vaswani 2017 | 4-head, 2-layer encoder |
| **Informer** | Sparse attention | Zhou 2021 | ProbSparse, factor=5 |
| **PatchTST** | Patch time series | Nie 2023 | Patch=16, stride=8 |
| **STGAT** | Spatial-temporal GAT | Graph attention | 2-layer GAT, 4 heads |
| **LAWS V2** | Ensemble (QG+PC3+CWT) | This work | Production binary |

## 3. Dataset & Split

| Split | Ratio | Years | Events |
|---|---|---|---|
| Training | 60% | 2015-2019 | ~XXX Mw>=5.0 |
| Validation | 20% | 2020-2021 | ~XXX |
| Test | 20% | 2022-2023 | ~XXX |

### Preprocessing (identical across models)
- Same station data, same interpolation
- Same normalization (z-score per station)
- Same window size (7-day input → predict next 14-day window)

## 4. Training Configuration
- Loss: Binary cross-entropy
- Optimizer: Adam (lr=1e-3, weight decay=1e-5)
- Early stopping: 10 epochs
- Batch size: 32
- Seed: Fixed per run (42, 43, 44 for 3-fold)

## 5. Inference & Metrics
All models evaluated with identical EPEF evaluation protocol:
- Threshold-independent: AUC-ROC, AUC-PR
- Threshold-dependent: Recall, Precision, F1 (at P=0.40)
- Statistical: 95% CI via bootstrap (n=2000)
- Significance: McNemar test comparing each baseline vs LAWS V2

## 6. Reporting Template
| Model | AUC-ROC | AUC-PR | Recall | Precision | F1 | FAR | Brier |
|---|---|---|---|---|---|---|---|
| CNN | | | | | | | |
| LSTM | | | | | | | |
| Transformer | | | | | | | |
| Informer | | | | | | | |
| PatchTST | | | | | | | |
| STGAT | | | | | | | |
| LAWS V2 | | | | | | | |
