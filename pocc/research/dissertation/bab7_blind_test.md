# Bab VII: Blind Prediction Test

## 7.1 EPEF Framework
Earthquake Prediction Evaluation Framework (EPEF) V1.0 dirancang sebagai standar evaluasi prediksi prekursor gempa.

### 7.1.1 Freeze Sequence
1. **Dataset Freeze**: SHA-256 manifest dari seluruh data historis BMKG
2. **Model Freeze**: Bobot LAWSV95Real + hyperparameter dikunci
3. **Protocol Freeze**: Metrik, gates, dan window evaluasi ditetapkan

### 7.1.2 Blind Execution
Inferensi dijalankan pada dataset frozen tanpa akses ke label (catalog gempa). Output berupa file JSONL immutable.

## 7.2 Dataset
- Sumber: 23 stasiun BMKG
- Periode: [training/validation/test split]
- Komponen: H, D, Z (geomagnetik) + LEM
- Label: BMKG catalog (Mw >= 5.0)

## 7.3 Evaluation Metrics

### Detection Metrics
- Recall, Precision, F1, FAR, CSI, HSS, GSS
- Contingency table: TP/FP/FN/TN

### Forecasting Metrics
- Brier Score, AUC-ROC, Log-Loss
- Reliability Diagram

### Lead Time Metrics
- Distribusi lead time per bin
- Mean, median, min, max
- Fraction > 24h, > 72h

## 7.4 Statistical Significance
- Permutation test: 1000x random timestamp shuffle
- Molchan Diagram: POD vs. space-time volume
- Bootstrap confidence intervals (95%, n=2000)

## 7.5 Expected Results
[SECTION TBD — akan diisi setelah blind test dieksekusi]
