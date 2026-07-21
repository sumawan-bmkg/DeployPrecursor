# Statistical Validation Framework — EPEF V1.0

## 1. McNemar Test
For paired binary classification comparison between two models:

\[
\chi^2 = \frac{(n_{12} - n_{21})^2}{n_{12} + n_{21}}
\]

Where $n_{12}$ = count where model A correct and B wrong, $n_{21}$ = reverse.

Significance: $\chi^2 > 3.84$ at $p < 0.05$ (df=1).

**Usage**: Compare each baseline vs LAWS V2 on identical test set.

---

## 2. Bootstrap Confidence Intervals
For any metric $M$ computed on sample of size $N$:

```
Algorithm:
1. For b = 1 to B (B=2000):
   a. Sample N observations WITH REPLACEMENT
   b. Compute M_b on resampled data
2. CI_95 = [percentile(M_b, 2.5%), percentile(M_b, 97.5%)]
```

Report: $\text{Metric} = M \pm [CI_{\text{lower}}, CI_{\text{upper}}]$

---

## 3. Permutation Test
For testing whether observed skill is better than chance:

```
Algorithm:
1. Compute observed metric M_obs on (predictions, labels)
2. For p = 1 to P (P=1000):
   a. Shuffle labels randomly
   b. Compute M_p on (predictions, shuffled_labels)
3. p_value = fraction of M_p >= M_obs
```

Reject H0 (no skill) if $p < 0.05$.

---

## 4. Wilcoxon Signed-Rank Test
Non-parametric paired test for lead time differences:

\[
W = \sum_{i=1}^{n} \text{sgn}(x_i - y_i) \cdot R_i
\]

Used when comparing lead time distributions across two models on same event set.

---

## 5. Effect Size (Cohen's d)
\[
d = \frac{\bar{X}_1 - \bar{X}_2}{s_{\text{pooled}}}
\]

| |d| | Interpretation |
|---|---|
| < 0.2 | Negligible |
| 0.2 - 0.5 | Small |
| 0.5 - 0.8 | Medium |
| > 0.8 | Large |

---

## 6. Calibration Analysis
Hosmer-Lemeshow test for probability calibration:

\[
HL = \sum_{k=1}^{K} \frac{(O_k - E_k)^2}{E_k}
\]

Where $O_k$ = observed events, $E_k$ = expected (predicted sum) in bin $k$.

Reject calibration if $HL > \chi^2_{0.05, K-2}$.

---

## 7. Reliability Diagram Construction
1. Sort predictions into $K=10$ equal bins: $[0, 0.1), [0.1, 0.2), \dots, [0.9, 1.0]$
2. For each bin $k$: $\bar{p}_k = \text{mean}(p_i)$, $\bar{o}_k = \text{mean}(o_i)$
3. Plot $\bar{p}_k$ vs $\bar{o}_k$ with 95% binomial confidence intervals
4. Perfect: $\bar{o}_k = \bar{p}_k$ (diagonal)
