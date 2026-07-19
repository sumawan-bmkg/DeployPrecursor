# Physics Validation Protocol

**Version:** 2.0
**Date:** 2026-07-16

---

## Purpose

Verify that model predictions are physically consistent with ULF earthquake precursor theory.

---

## 1. H/D/Z Component Analysis

### 1.1 Vertical Component Dominance

**Theory:** Deep earthquake preparation produces stronger Z-component anomalies at the surface than H-component anomalies, due to evanescent decay of horizontal fields.

**Test:**
1. For each true positive prediction, compute power in H, D, Z components during the 24h before event
2. Compute Z/H ratio
3. Compare to Z/H ratio during quiet periods

**Expected:** Z/H ratio during precursor periods > Z/H ratio during quiet periods

### 1.2 H/Z Ratio Tracking

**Theory:** Decreasing H/Z ratio indicates increasing vertical magnetic field contribution, consistent with subsurface source.

**Test:** Plot H/Z ratio time series for each TP. Verify that H/Z decreases in the hours/days before the event.

---

## 2. Polarization Analysis

### 2.1 Polarization Ratio

**Theory:** Linearly polarized ULF signals are associated with tectonic sources; circularly polarized signals are more likely magnetospheric.

**Formula:** Polarization ratio = Z / √(H² + D²)

**Test:**
1. Compute polarization ratio during TP periods
2. Compute during quiet periods
3. Compare distributions

**Expected:** Higher polarization ratio during precursor periods

### 2.2 Polarization Plane Rotation

**Theory:** The polarization plane may rotate during earthquake preparation as the source geometry evolves.

**Test:** Plot polarization angle (atan2(D,H)) time series during TP periods. Look for systematic rotation.

---

## 3. Spectral Evolution

### 3.1 Pc3 Band (0.022-0.1 Hz)

**Theory:** Pc3 pulsations may be modulated by earthquake preparation.

**Test:** Compute spectral power in Pc3 band during TP periods vs quiet periods.

### 3.2 Pc4 Band (0.0067-0.022 Hz)

**Same approach as 3.1 but for Pc4 band.**

### 3.3 Spectral Migration

**Theory:** Precursor signals may show progressive spectral energy migration from higher to lower frequencies as stress increases.

**Test:** Plot spectrograms centered on each event. Look for low-frequency energy enhancement in the 24h before the event.

---

## 4. Geomagnetic Index Correlation

### 4.1 Dst Correlation

**Test:** Compute correlation between prediction confidence and Dst index.

**Expected:** Low correlation (|r| < 0.3) if predictions are tectonic, not magnetospheric.

### 4.2 Kp Correlation

**Same approach as 4.1 but for Kp.**

### 4.3 AE Correlation

**Same approach as 4.1 but for AE (auroral electrojet index).**

**Critical:** If any of these correlations are > 0.5, the model is strongly influenced by magnetospheric activity.

---

## 5. EEJ Assessment

### 5.1 Station Magnetic Latitude

**Compute:** Geographic and geomagnetic latitude for all 21 prediction-capable stations.

**Flag:** Any station within ±3° of the geomagnetic equator.

**Correction if flagged:** Apply Sq/EEJ removal using reference station method or solar zenith angle correction.

### 5.2 Daytime vs Nighttime Analysis

**Test:** Compare FAR between daytime (06-18 LT) and nighttime (18-06 LT).

**Expected:** If EEJ is not properly removed, daytime FAR >> nighttime FAR.

---

## 6. Diurnal Variation Assessment

### 6.1 Quiet-Day Curve

**Theory:** The quiet-day solar variation (Sq) has characteristic shape at each station.

**Test:** Plot the model's confidence as a function of local time on quiet days. If confidence shows strong diurnal pattern, the model may be learning Sq, not precursors.

---

## 7. Checklist

| Check | Pass | Evidence |
|-------|------|----------|
| Z/H ratio during TP > quiet | | |
| Polarization ratio higher during TP | | |
| Spectral power in Pc3/Pc4 during TP | | |
| Dst correlation < 0.3 | | |
| Kp correlation < 0.3 | | |
| AE correlation < 0.3 | | |
| Station magnetic latitudes documented | | |
| EEJ correction applied if needed | | |
| Day/night FAR ratio < 2.0 | | |
| Quiet-day confidence shows no diurnal pattern | | |
