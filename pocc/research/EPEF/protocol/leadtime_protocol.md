# Lead Time Analysis Protocol — EPEF V1.0

## 1. Definition
Lead time is the interval between a validated prediction timestamp ($T_{\text{pred}}$) and the actual earthquake onset time ($T_{\text{eq}}$):

\[
\Delta t_{\text{lead}} = T_{\text{eq}} - T_{\text{pred}}
\]

### 1.1 Temporal Resolution
| Category | Range | Resolution |
|---|---|---|
| Short | 1–24 hours | Hourly bins |
| Medium | 1–7 days | Daily bins |
| Long | 7–14 days | Daily bins |

### 1.2 Lead Time Bins
\[
B_k: [2^k, 2^{k+1}) \text{ hours}, \quad k = 0,1,\dots,9
\]
Spanning 1 hour to ~512 hours (21 days).

---

## 2. Statistical Significance

### 2.1 Baseline Comparison
- **Random**: Bootstrap $n=10000$ random prediction timestamps, compute lead time distribution.
- **Persistence**: Use previous interval prediction as naive forecast.
- **Significance**: Fraction of random permutations achieving lead time $\ge$ observed.

### 2.2 Molchan Diagram
Scoring: probability of detection $P_d$ vs. space-time volume $V$ at different lead time thresholds.

### 2.3 Skill Score
\[
SS_{\text{lead}} = \frac{\text{Lead}_{\text{model}} - \text{Lead}_{\text{baseline}}}{\text{Lead}_{\text{perfect}} - \text{Lead}_{\text{baseline}}}
\]

---

## 3. Operational Requirement
- Minimum lead time: 24 hours (BMKG operational requirement)
- Target lead time: 72 hours (MO1)
- Stretch lead time: 168 hours (MO2)
