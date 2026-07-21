# Detection Metrics — EPEF V1.0

## 1. Ground-Truth Matching Logic

```mermaid
flowchart TD
    A[Prediction issued] --> B[Time window: +14 days]
    B --> C[Space window: < 500 km]
    C --> D{Event in catalog?}
    D -->|Yes, Mw >= 5.0| E[TRUE POSITIVE]
    D -->|Yes, Mw < 5.0| F[FALSE POSITIVE]
    D -->|No event| F
    E --> G[Compute lead time]
    F --> H[False alarm recorded]
```

## 2. Contingency Table

| | Event Observed | No Event |
|---|---|---|
| **Predicted** | TP | FP |
| **Not Predicted** | FN | TN |

## 3. Core Metrics

### 3.1 Detection Rate (Recall)
\[
\text{Recall} = \frac{TP}{TP + FN}
\]

### 3.2 Precision
\[
\text{Precision} = \frac{TP}{TP + FP}
\]

### 3.3 F1 Score
\[
F_1 = 2 \cdot \frac{P \cdot R}{P + R}
\]

### 3.4 False Alarm Rate
\[
\text{FAR} = \frac{FP}{TP + FP}
\]

### 3.5 Miss Rate
\[
\text{Miss} = \frac{FN}{TP + FN} = 1 - \text{Recall}
\]

### 3.6 Critical Success Index (CSI)
\[
\text{CSI} = \frac{TP}{TP + FP + FN}
\]

### 3.7 Probability of Detection (POD)
\[
\text{POD} = \frac{TP}{TP + FN}
\]

### 3.8 Heidke Skill Score (HSS)
\[
\text{HSS} = \frac{2(TP \cdot TN - FP \cdot FN)}{(TP + FN)(FN + TN) + (TP + FP)(FP + TN)}
\]

### 3.9 Gilbert Skill Score (GSS)
\[
\text{GSS} = \frac{TP - TP_{\text{random}}}{TP - FP - FN + TP_{\text{random}}}
\]

---

## 4. Required Thresholds for Blind Test
| Metric | Threshold | Target |
|---|---|---|
| Recall | $\ge 0.60$ | $\ge 0.75$ |
| Precision | $\ge 0.40$ | $\ge 0.60$ |
| F1 | $\ge 0.40$ | $\ge 0.65$ |
| FAR | $\le 0.60$ | $\le 0.40$ |
| CSI | $\ge 0.30$ | $\ge 0.50$ |
| HSS | $\ge 0.40$ | $\ge 0.60$ |
