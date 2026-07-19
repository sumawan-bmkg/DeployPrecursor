# EEJ Classification Report

**Generated:** 2026-07-16
**Purpose:** Classify all BMKG stations by Equatorial Electrojet (EEJ) influence zone.

---

## 1. EEJ Background

The Equatorial Electrojet (EEJ) is a strong (~100 nT at noon) eastward electric current in the E-region ionosphere within ±3° of the geomagnetic dip equator. It produces:
- Daytime enhancement of horizontal magnetic field (H-component)
- Strong diurnal variation (peak near local noon)
- Seasonal variation (strongest during equinox)
- Minimum at night

**Implication for ULF precursor detection:**
Stations within the EEJ band will have daytime H-component variations up to 100 nT — same order of magnitude as expected ULF precursors. Without EEJ correction, anomalies detected by the model during daytime at EEJ stations are indistinguishable from EEJ variations.

---

## 2. Station Magnetic Latitude Calculation

### Method
- Use IGRF-13 geomagnetic field model
- Compute geomagnetic latitude for each station
- Classify: EEJ core (±3°), EEJ transition (3-5°), non-EEJ (>5°)

### Stations to classify

| Station | Geographic Lat | Geographic Lon | Geomagnetic Lat | EEJ Zone |
|---------|---------------|----------------|-----------------|----------|
| ALR | -8.25 | 124.38 | | |
| AMB | -3.70 | 128.17 | | |
| CLP | -6.55 | 106.63 | | |
| DNP | -8.67 | 115.22 | | |
| GTO | 0.57 | 122.91 | | |
| KPY | -7.73 | 110.61 | | |
| LPS | -5.04 | 104.00 | | |
| LUT | -4.18 | 126.17 | | |
| LWA | -8.37 | 122.97 | | |
| LWK | -8.13 | 117.63 | | |
| MLB | -7.95 | 112.63 | | |
| PLU | -5.70 | 105.70 | | |
| SBG | -3.35 | 117.50 | | |
| SCN | -6.83 | 110.87 | | |
| SKB | -7.50 | 110.35 | | |
| SMI | -8.57 | 115.28 | | |
| SRG | -7.00 | 110.43 | | |
| SRO | -7.52 | 110.87 | | |
| TNT | -7.88 | 112.52 | | |
| TRT | -5.27 | 103.89 | | |
| YOG | -7.78 | 110.38 | | |

---

## 3. EEZ Zone Definitions

### EEJ Core (±3° magnetic latitude)
- Daytime H-component enhancement: 50-100 nT at noon
- Diurnal variation: strong (peak at ~12 LT)
- **Risk:** Very high — predictions during daytime cannot be trusted without correction
- Stations in this zone: (fill from calculation)

### EEJ Transition (3-5° magnetic latitude)
- Daytime H-component enhancement: 10-50 nT
- Diurnal variation: moderate
- **Risk:** Moderate — may need partial correction
- Stations in this zone: (fill)

### Non-EEJ (>5° magnetic latitude)
- Daytime H-component enhancement: <10 nT
- Diurnal variation: weak
- **Risk:** Low — standard external field correction sufficient
- Stations in this zone: (fill)

---

## 4. Implications for Blind Test

| Zone | Correction Required | Impact on Model |
|------|--------------------|-----------------|
| EEJ Core | Yes — EEJ removal via reference station or solar zenith model | Predictions during daytime (06-18 LT) must be flagged or excluded |
| EEJ Transition | Optional — reference station difference method | Reduced confidence for daytime predictions |
| Non-EEJ | No — standard quiet-day normalization | Predictions usable at all times |

## 5. Recommended EEJ Mitigation

### Option A: Reference Station Difference
Use a non-EEJ reference station (if available outside core) and subtract its horizontal field from the EEJ station.

### Option B: Solar Zenith Angle Correction
Model the EEJ strength as a function of solar zenith angle and local time, subtract from data.

### Option C: Exclude Daytime for Core Stations
For blind test, exclude predictions during 08-16 LT for EEJ core stations. This is the safest but reduces data availability.

---

## 6. Recommendation

Before blind test:
1. Compute geomagnetic latitude for all 21 stations
2. If any core-EEJ stations found with priors, document the mitigation strategy
3. Stratify all blind test metrics by EEJ zone (core/transition/non-EEJ)
4. Report FAR separately for daytime vs nighttime at core stations
