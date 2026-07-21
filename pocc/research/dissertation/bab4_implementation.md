# Bab IV: Implementasi Sistem LAWS V2

## 4.1 Arsitektur Sistem
Sistem LAWS V2 dibangun dengan arsitektur pipeline 6 worker yang berjalan secara siklik:

1. **Discovery Worker** (periode: 300 detik) — Mendeteksi ketersediaan data baru dari server FTP BMKG
2. **Download Worker** (600 detik) — Mengunduh data magnetometer dan LEM ke lokal
3. **Validation Worker** (60 detik) — Verifikasi integritas data menggunakan CRC32
4. **Inference Worker** (60 detik) — Eksekusi model prediksi LAWSV95Real
5. **Audit Worker** (3600 detik) — Audit prediksi dan evaluasi berkala
6. **Evidence Worker** (86400 detik) — Pembangkitan bukti harian

## 4.2 Implementasi QG Analysis
Metode Quasi-Geomagnetic (QG) index mengukur rasio komponen polarisasi sebagai indikator aktivitas seismik:

\[
QG = \frac{|H|}{|D| + |Z|}
\]

Dimana H, D, Z adalah komponen medan geomagnetik. Peningkatan QG menunjukkan kemungkinan anomali prekursor.

## 4.3 Implementasi PC3 Analysis
Pulsasi Pc3 (periode 10-45 detik) dianalisis melalui band-pass filter:

```python
# Band-pass filter 0.022-0.1 Hz (Pc3 range)
sos = signal.butter(4, [0.022, 0.1], btype='band', fs=1.0, output='sos')
filtered = signal.sosfilt(sos, data)
amplitude = np.sqrt(np.mean(filtered**2))
```

## 4.4 Implementasi CWT Scalogram
Transformasi wavelet kontinu menggunakan Morlet mother wavelet:

\[
W(a,b) = \frac{1}{\sqrt{a}} \int s(t) \psi^*\left(\frac{t-b}{a}\right) dt
\]

Scalogram: \(|W(a,b)|^2\) sebagai input ke ensemble predictor.

## 4.5 Pipeline Prediksi
Setiap trigger file memicu inferensi penuh:
1. Parse trigger → station + timestamp
2. LAWSRealPredictor.predict() → Prediction
3. save_prediction(PG)
4. DecisionEngine.evaluate() → Decision
5. save_decision(PG)
6. Station fusion (500km, 2h) → FusedEvent
7. EventManager → WarningManager

## 4.6 Decision Engine
4-level decision gates:
- ProbabilityThreshold: 0.40 (ADVISORY) / 0.70 (WATCH) / 0.90 (WARNING)
- QCConsistency: minimum 0.50
- UncertaintyGate: maximum 0.50
- StormGate: suppress saat Kp > 4

## 4.7 Station Fusion
Algoritma fusi spasial-temporal:
1. Query semua prediksi dalam 2 jam
2. Filter radius 500km haversine
3. Minimum 2 stasiun untuk event
4. Weighted fusion: \(P_{\text{fused}} = \frac{\sum w_i P_i}{\sum w_i}\)
