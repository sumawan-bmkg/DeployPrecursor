# Forecasting Metrics — EPEF V1.0

## 1. Probability Forecast Evaluation

### 1.1 Brier Score
\[
BS = \frac{1}{N}\sum_{i=1}^N (p_i - o_i)^2
\]
where $p_i \in [0,1]$ is predicted probability and $o_i \in \{0,1\}$ is observed outcome.

### 1.2 Brier Skill Score
\[
BSS = 1 - \frac{BS}{BS_{\text{climatology}}}
\]

### 1.3 Log-Loss
\[
\text{LogLoss} = -\frac{1}{N}\sum_{i=1}^N [o_i \ln(p_i) + (1-o_i)\ln(1-p_i)]
\]

---

## 2. Discrimination

### 2.1 AUC-ROC
Area under the Receiver Operating Characteristic curve: $P(\text{score}_{\text{event}} > \text{score}_{\text{non-event}})$.

### 2.2 AUC-PR
Area under Precision-Recall curve. Preferred for imbalanced datasets.

---

## 3. Reliability and Sharpness

### 3.1 Reliability Diagram
Binned probability forecasts ($K=10$ bins):
\[
\bar{o}_k = \frac{1}{N_k}\sum_{i \in B_k} o_i, \quad k = 1, \dots, K
\]
Perfect reliability: $\bar{o}_k = p_k$.

### 3.2 Reliability Component
\[
\text{Rel} = \frac{1}{N}\sum_{k=1}^K N_k (p_k - \bar{o}_k)^2
\]

### 3.3 Sharpness
\[
\text{Sharpness} = \frac{1}{N}\sum_{i=1}^N (p_i - 0.5)^2
\]

### 3.4 Resolution
\[
\text{Res} = \frac{1}{N}\sum_{k=1}^K N_k (\bar{o}_k - \bar{o})^2
\]

---

## 4. Calibration Curves
Construction: Sort predictions, form $K$ equal-sized bins. Plot $\bar{p}_k$ vs. $\bar{o}_k$ with 95% confidence intervals via bootstrap.
