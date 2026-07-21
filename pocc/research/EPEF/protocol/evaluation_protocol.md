# Evaluation Protocol — EPEF V1.0

## 1. Blind vs. Operational Evaluation
Two distinct evaluation regimes are defined:

| Dimension | Blind (Retrospective) | Operational (Prospective) |
|---|---|---|
| Dataset Window | Historical (frozen) | Continuous streaming |
| Model | Frozen weights | Production binary |
| Lead Time | Post hoc computed | Real-time clock |
| Ground Truth | BMKG catalog (known) | Future observations |
| Gate | Publication / Regulatory | Pilot Operation sign-off |

---

## 2. Scoring Gates

### 2.1 Detection Gate
\[
\text{Detection} = 
\begin{cases}
\text{TRUE}, & \text{if } M_w \ge 5.0 \land R \le 500 \text{ km} \land T_{\text{lead}} \ge 24\text{h}\\
\text{FALSE}, & \text{otherwise}
\end{cases}
\]

### 2.2 Confidence Scoring
\[
\text{Confidence} = \frac{N_{\text{stations}, P \ge 0.40}}{N_{\text{stations, total}}}
\]

### 2.3 Event Window
\[
T_{\text{window}} = [T_{\text{prediction}}, T_{\text{prediction}} + 14 \text{ days}]
\]
Matching: spatial (500 km haversine) + temporal (14 days).

---

## 3. Evaluation Metrics Hierarchy

### Detection & Forecasting
| Metric | Equation | Good |
|---|---|---|
| Recall (TPR) | $TP / (TP + FN)$ | > 0.60 |
| Precision | $TP / (TP + FP)$ | > 0.40 |
| F1 | $2 \cdot P \cdot R / (P + R)$ | > 0.40 |
| FAR | $FP / (TP + FP)$ | < 0.60 |

### Calibration
| Metric | Equation | Good |
|---|---|---|
| Brier Score | $\frac{1}{N}\sum (p_i - o_i)^2$ | < 0.10 |
| Reliability | $\sum n_k (p_k - \bar{o}_k)^2 / N$ | < 0.05 |
| AUC-ROC | $\int \text{TPR}(FPR) dFPR$ | > 0.70 |

### Lead Time
| Metric | Definition | Good |
|---|---|---|
| Mean Lead | $\frac{1}{N}\sum (T_{\text{event}} - T_{\text{prediction}})$ | > 72h |
| Lead>24h | Fraction | > 0.80 |
| Lead>72h | Fraction | > 0.50 |

---

## 4. Statistical Significance

- **Randomization test**: 1000x permutation of timestamps.
- **Molchan Diagram**: probability vs. space-time volume.
- **Skill Score**: $SS_{\text{ROC}} = (AUC - 0.5) / (1.0 - 0.5)$.

All metrics shall be reported with 95% confidence intervals (bootstrap, $n=2000$).
