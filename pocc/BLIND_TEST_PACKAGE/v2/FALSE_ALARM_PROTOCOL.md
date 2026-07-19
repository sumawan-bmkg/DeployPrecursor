# False Alarm Protocol

**Version:** 2.0
**Date:** 2026-07-16

---

## Purpose

Systematically characterize and quantify false alarms. A system that alarms during storms or quiet periods is not detecting precursors.

---

## 1. False Alarm Categories

| Category | Definition | Expected FAR |
|----------|-----------|--------------|
| Quiet Days | Dst > -20 nT, Kp < 3, no M≥4 within 7 days | Lowest |
| Storm Days | Dst < -50 nT | Should be flagged |
| Severe Storm | Dst < -100 nT | Should be suppressed |
| Solar Active | Kp > 6 | Should be suppressed |
| EEJ Active | Daytime (06-18 LT) near magnetic equator | Should be investigated |
| Post-Seismic | Within 72h of M≥5.0, D<100km | Should be excluded |

---

## 2. False Alarm Metrics

### 2.1 False Alarm Rate (FAR)

FAR = FP / (FP + TN) = number of false alarms / total non-event periods

**Report as:** per-day FAR, per-station FAR

### 2.2 Alarm Duration

How long does a false alarm persist once triggered?

Average duration = mean number of consecutive prediction windows flagged as alarm.

If duration > 6 hours, the alarm may be a persistent environmental artifact rather than a short precursor.

### 2.3 Alarm Density

Alarm density = number of alarms per station per day

Compare to:
- Storm days (expect higher density)
- Quiet days (expect lower density)

### 2.4 Warning Efficiency

Warning Efficiency = TP / (TP + FP + FN)

This penalizes both missed events and false alarms.

---

## 3. Stratified FAR Analysis

For each Dst bin, compute FAR independently:

| Dst Range | FAR | Classification |
|-----------|-----|----------------|
| Dst > -20 | | Quiet |
| -20 > Dst > -50 | | Moderate |
| -50 > Dst > -100 | | Storm |
| Dst < -100 | | Severe storm |

**Critical test:** If FAR(storm) > 2 × FAR(quiet), the model is storm-sensitive and predictions during storms are suspect.

---

## 4. Diurnal FAR Analysis

| Local Time | FAR | Classification |
|------------|-----|----------------|
| 00-06 | | Night (quiet ionosphere) |
| 06-12 | | Morning (EEJ active) |
| 12-18 | | Afternoon (EEJ active) |
| 18-24 | | Evening (ionosphere quieting) |

**Critical test:** If FAR(day) > 2 × FAR(night), possible EEJ/Sq contamination.

---

## 5. Post-Seismic Exclusion

- Exclude all predictions within 48 hours of any M ≥ 5.0 mainshock within 500 km of the prediction station
- Document excluded count
- Report FAR with and without post-seismic exclusion

---

## 6. Non-Earthquake Day Analysis

Define "non-earthquake days" as days with:
- No M ≥ 3.5 event within 1000 km of any station
- Dst > -30 nT
- Kp < 4

Compute:
- Number of predictions on non-earthquake days
- Fraction of all predictions that are on non-earthquake days
- Average confidence on non-earthquake days vs. true-positive days

If average confidence on non-earthquake days is similar to TP days, the model is not discriminating.
