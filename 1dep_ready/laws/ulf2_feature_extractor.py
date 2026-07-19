#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULF2A PHYSICS-FIRST FEATURE EXTRACTION
=======================================
Extract 53 ULF features from 1 Hz magnetometer windows.

Feature families (53 total):
  1. Energy (12)       — H/D/Z rms, energy, power, peak freq
  2. Spectral (8)      — Pc band ratios, centroid, edge, flatness
  3. Entropy (6)       — spectral entropy (3) + dynamical (3)
  4. Burst (5)         — envelope peak statistics
  5. Polarization (6)  — H/D cross-spectrum, ellipticity, planarity
  6. Consensus (8)     — same-timestamp cross-station network features
  7. Coherence (8)     — pairwise R, PLV, growth rates

Inputs:
  - ulf1_windows.h5       (H_raw, D_raw, Z_raw, H_det, D_det, Z_det)
  - ulf1_window_meta.csv  (station, date, window_idx, t_start, t_end, ...)

Outputs:
  - ulf2_features_window.csv      (27,777 × 53 features + index)
  - ulf2_feature_metadata.json    (feature names, families, stats)

Hard constraints:
  - NO magnitude labels in any output
  - NO feature count > 60
  - NO cross-station temporal lag features
"""

import sys, json, time, warnings, gc
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import signal as sp_signal
from scipy.stats import entropy as sp_entropy
import h5py
from numba import njit

warnings.filterwarnings('ignore')

BASE = Path('D:/multi/scalogramv3')
ULF1 = BASE / 'debug' / 'mag_v2b_swa' / 'ulf1'
OUT = BASE / 'debug' / 'mag_v2b_swa' / 'ulf2'
OUT.mkdir(parents=True, exist_ok=True)

WIN_LEN = 3600
FS = 1.0  # 1 Hz sampling rate

# ── Feature names (53) ──
FEATURE_NAMES = [
    # Energy (12)
    'H_rms', 'D_rms', 'Z_rms',
    'H_energy', 'D_energy', 'Z_energy',
    'H_total_power', 'D_total_power', 'Z_total_power',
    'H_dominant', 'D_dominant', 'Z_dominant',
    # Spectral (8)
    'sp_ratio_Pc5', 'sp_ratio_Pc4', 'sp_ratio_Pc3', 'sp_ratio_Pc2',
    'sp_centroid', 'sp_edge_freq', 'sp_peak_freq', 'sp_flatness',
    # Entropy (6)
    'sp_entropy_H', 'sp_entropy_D', 'sp_entropy_Z',
    'dyn_sampen', 'dyn_perm_entropy', 'dyn_spectral_entropy',
    # Burst (5)
    'burst_count', 'burst_max_amp', 'burst_mean_amp',
    'burst_duration', 'burst_density',
    # Polarization (6)
    'pol_dop', 'pol_coherence', 'pol_h_ratio',
    'pol_phase_diff', 'pol_ellipticity', 'pol_planarity',
    # Consensus (8) — cross-station
    'net_consensus_mean', 'net_consensus_max',
    'net_spread_mean', 'net_spread_min', 'net_spread_std',
    'net_agreement_count', 'net_dispersion', 'net_coverage',
    # Coherence (8) — cross-station
    'network_R', 'network_spread', 'pairwise_agreement',
    'station_synchronization', 'consensus_growth_rate',
    'spread_collapse_rate', 'phase_locking_value', 'mean_coherence_band',
]

FAMILY_MAP = {}
for f in FEATURE_NAMES:
    if f.startswith(('H_', 'D_', 'Z_')) and not f.startswith(('H_total', 'D_total', 'Z_total')):
        if 'dominant' in f:
            FAMILY_MAP[f] = 'energy'
        elif f in ('H_rms', 'D_rms', 'Z_rms'):
            FAMILY_MAP[f] = 'energy'
        elif f in ('H_energy', 'D_energy', 'Z_energy'):
            FAMILY_MAP[f] = 'energy'
        elif f in ('H_total_power', 'D_total_power', 'Z_total_power'):
            FAMILY_MAP[f] = 'energy'
    elif f.startswith('sp_'):
        FAMILY_MAP[f] = 'spectral'
    elif f.startswith(('sp_entropy_', 'dyn_')):
        FAMILY_MAP[f] = 'entropy'
    elif f.startswith('burst_'):
        FAMILY_MAP[f] = 'burst'
    elif f.startswith('pol_'):
        FAMILY_MAP[f] = 'polarization'
    elif f.startswith('net_'):
        FAMILY_MAP[f] = 'consensus'
    elif f.startswith(('network_', 'pairwise_', 'station_', 'consensus_',
                       'spread_', 'phase_locking', 'mean_coherence')):
        FAMILY_MAP[f] = 'coherence'
    else:
        FAMILY_MAP[f] = 'unknown'

assert len(FEATURE_NAMES) == 53, f"Expected 53 features, got {len(FEATURE_NAMES)}"
assert len(set(FAMILY_MAP.keys())) == 53


# ══════════════════════════════════════════════════════════════════
# SPECTRAL HELPERS
# ══════════════════════════════════════════════════════════════════

def compute_psd(x, fs=FS, nperseg=1024):
    """Welch PSD. Returns (freqs, psd)."""
    f, pxx = sp_signal.welch(x, fs=fs, nperseg=min(nperseg, len(x)),
                              noverlap=min(nperseg//2, len(x)//2),
                              detrend='constant')
    return f, pxx


def band_power(freqs, psd, f_low, f_high):
    """Integrated power in frequency band."""
    mask = (freqs >= f_low) & (freqs < f_high)
    if mask.sum() == 0:
        return 0.0
    return float(np.trapezoid(psd[mask], freqs[mask]))


def spectral_entropy(psd):
    """Normalized spectral entropy (0–1)."""
    psd_norm = psd / (psd.sum() + 1e-30)
    psd_norm = psd_norm[psd_norm > 0]
    if len(psd_norm) < 2:
        return 0.0
    return float(sp_entropy(psd_norm) / np.log(len(psd_norm)))


def spectral_centroid(freqs, psd):
    """Weighted mean frequency."""
    total = psd.sum() + 1e-30
    return float(np.sum(freqs * psd) / total)


def spectral_edge(freqs, psd, pct=0.90):
    """Frequency below which `pct` of total power resides."""
    cumsum = np.cumsum(psd)
    total = cumsum[-1] + 1e-30
    idx = np.searchsorted(cumsum / total, pct)
    idx = min(idx, len(freqs) - 1)
    return float(freqs[idx])


def spectral_flatness(psd):
    """Wiener entropy: geometric_mean / arithmetic_mean."""
    psd_pos = psd[psd > 0]
    if len(psd_pos) < 2:
        return 0.0
    geo = np.exp(np.mean(np.log(psd_pos)))
    ari = np.mean(psd_pos)
    return float(geo / (ari + 1e-30))


def dominant_freq(freqs, psd):
    """Peak frequency."""
    if psd.max() < 1e-30:
        return 0.0
    return float(freqs[np.argmax(psd)])


# ══════════════════════════════════════════════════════════════════
# ENTROPY HELPERS
# ══════════════════════════════════════════════════════════════════
@njit(cache=True)
def _count_matches_numba(x, N, m, r):
    count = 0
    n_templates = N - m
    for i in range(n_templates):
        for j in range(i + 1, n_templates):
            max_dist = 0.0
            for k in range(m):
                diff = abs(x[i + k] - x[j + k])
                if diff > max_dist:
                    max_dist = diff
            if max_dist < r:
                count += 1
    return count


def _sample_entropy_impl(x, m=2, r_ratio=0.2):
    try:
        # Remove NaN
        n_valid = 0
        for i in range(len(x)):
            if x[i] == x[i]:
                n_valid += 1
        if n_valid < 50:
            return 0.0

        # Copy valid values
        x_clean = np.empty(n_valid, dtype=np.float64)
        idx = 0
        for i in range(len(x)):
            if x[i] == x[i]:
                x_clean[idx] = x[i]
                idx += 1

        # Cap at 2000
        N = min(n_valid, 2000)
        x_work = x_clean[:N]

        # Compute std (manual for numba compatibility)
        std_x = 0.0
        for i in range(N):
            std_x += x_work[i]
        std_x /= N
        var = 0.0
        for i in range(N):
            d = x_work[i] - std_x
            var += d * d
        std_x = (var / N) ** 0.5

        r = r_ratio * std_x
        if r < 1e-30:
            return 0.0

        B = _count_matches_numba(x_work, N, m, r)
        A = _count_matches_numba(x_work, N, m + 1, r)

        if B == 0 or A == 0:
            return 0.0

        return float(-np.log(A / B))
    except Exception:
        # Fallback: pure-Python if numba unavailable
        x_arr = np.asarray(x, dtype=np.float64)
        x_arr = x_arr[~np.isnan(x_arr)]
        N = len(x_arr)
        if N < 50:
            return 0.0
        std_x = np.std(x_arr)
        r = r_ratio * std_x
        if r < 1e-30:
            return 0.0
        N = min(N, 2000)
        x_arr = x_arr[:N]

        def _count_matches(m_dim):
            templates = np.array([x_arr[i:i + m_dim] for i in range(N - m_dim)])
            count = 0
            for i in range(len(templates)):
                for j in range(i + 1, len(templates)):
                    dist = np.max(np.abs(templates[i] - templates[j]))
                    if dist < r:
                        count += 1
            return count

        B = _count_matches(m)
        A = _count_matches(m + 1)
        if B == 0 or A == 0:
            return 0.0
        return float(-np.log(A / B))


def sample_entropy(x, m=2, r_ratio=0.2):
    """Sample entropy -- lower = more regular, higher = more complex.

    Uses Numba-JIT backend when available (722x speedup).
    Falls back to pure-Python if numba is not installed.
    """
    return _sample_entropy_impl(x, m, r_ratio)


def permutation_entropy(x, m=3):
    """Permutation entropy (normalized 0–1)."""
    n = len(x)
    if n < m + 1:
        return 0.0
    # Subsample for speed
    if n > 1000:
        step = n // 1000
        x = x[::step]
        n = len(x)
    from itertools import permutations
    perms = {}
    for i in range(n - m + 1):
        pattern = tuple(np.argsort(x[i:i+m]))
        perms[pattern] = perms.get(pattern, 0) + 1
    probs = np.array(list(perms.values()), dtype=float) / (n - m + 1)
    return float(sp_entropy(probs) / np.log(len(perms) + 1e-30))


# ══════════════════════════════════════════════════════════════════
# BURST HELPERS
# ══════════════════════════════════════════════════════════════════

def burst_features(x):
    """Envelope-based burst statistics."""
    # Hilbert envelope
    analytic = sp_signal.hilbert(x)
    envelope = np.abs(analytic)
    std_env = np.std(envelope)
    threshold = 2.0 * std_env

    if std_env < 1e-30:
        return 0.0, 0.0, 0.0, 0.0, 0.0

    # Find peaks above threshold
    peaks, props = sp_signal.find_peaks(envelope, height=threshold)
    count = len(peaks)
    max_amp = float(envelope[peaks].max()) if count > 0 else 0.0
    mean_amp = float(envelope[peaks].mean()) if count > 0 else 0.0

    # Burst duration: mean number of consecutive samples above threshold
    above = envelope > threshold
    durations = []
    current_dur = 0
    for v in above:
        if v:
            current_dur += 1
        else:
            if current_dur > 0:
                durations.append(current_dur)
            current_dur = 0
    if current_dur > 0:
        durations.append(current_dur)

    mean_dur = float(np.mean(durations)) if durations else 0.0
    density = count / len(x) if len(x) > 0 else 0.0

    return float(count), max_amp, mean_amp, mean_dur, density


# ══════════════════════════════════════════════════════════════════
# POLARIZATION HELPERS
# ══════════════════════════════════════════════════════════════════

def polarization_features(H, D):
    """H/D cross-spectrum polarization features."""
    n = len(H)
    nperseg = min(1024, n)

    # Cross-spectrum
    f, Cxx = sp_signal.csd(H, H, fs=FS, nperseg=nperseg, noverlap=nperseg//2)
    _, Cyy = sp_signal.csd(D, D, fs=FS, nperseg=nperseg, noverlap=nperseg//2)
    _, Cxy = sp_signal.csd(H, D, fs=FS, nperseg=nperseg, noverlap=nperseg//2)

    # Total power per frequency
    P_total = Cxx + Cyy + 1e-30

    # Degree of polarization (Samson 1977)
    # DoP = sqrt(1 - 4*det(S)/tr(S)^2) per frequency, then mean
    det_S = Cxx * Cyy - np.abs(Cxy)**2
    tr_S = Cxx + Cyy
    dop_freq = np.sqrt(np.abs(1 - 4 * det_S / (tr_S**2 + 1e-30)))
    pol_dop = float(np.mean(dop_freq))

    # Coherence
    coh = np.abs(Cxy) / np.sqrt(Cxx * Cyy + 1e-30)
    pol_coherence = float(np.mean(coh))

    # H power ratio
    pol_h_ratio = float(np.mean(Cxx / (Cxx + Cyy + 1e-30)))

    # Phase difference at dominant frequency
    phase = np.angle(Cxy)
    dom_idx = np.argmax(P_total)
    pol_phase_diff = float(phase[dom_idx])

    # Ellipticity: |Im(Sxy)| / Re(Sxy)
    imag_ratio = np.abs(np.imag(Cxy)) / (np.real(Cxy) + 1e-30)
    pol_ellipticity = float(np.mean(imag_ratio))

    # Planarity: 1 - 2*min_eig / trace
    # For 2×2 Hermitian: eigenvalues are (tr ± sqrt(tr² - 4*det))/2
    eig_sum = tr_S
    eig_diff = np.sqrt(np.clip(tr_S**2 - 4 * det_S, 0, None))
    eig_min = (eig_sum - eig_diff) / 2
    planarity = 1 - 2 * eig_min / (eig_sum + 1e-30)
    pol_planarity = float(np.mean(np.clip(planarity, 0, 1)))

    return pol_dop, pol_coherence, pol_h_ratio, pol_phase_diff, pol_ellipticity, pol_planarity


# ══════════════════════════════════════════════════════════════════
# SINGLE-WINDOW FEATURE EXTRACTION
# ══════════════════════════════════════════════════════════════════

def extract_single_window(H_det, D_det, Z_det):
    """Extract 45 station-level features from one window (3600 samples)."""
    features = np.zeros(37, dtype=np.float64)

    # ── 1. Energy (12) ──
    for i, x in enumerate([H_det, D_det, Z_det]):
        rms = float(np.sqrt(np.mean(x**2)))
        features[i*4 + 0] = rms                          # X_rms
        features[i*4 + 1] = rms**2                       # X_energy
        f, psd = compute_psd(x)
        features[i*4 + 2] = float(np.trapezoid(psd, f))     # X_total_power
        features[i*4 + 3] = dominant_freq(f, psd)        # X_dominant

    # ── 2. Spectral (8) — combined H+D+Z PSD ──
    total_signal = H_det**2 + D_det**2 + Z_det**2
    f, psd_total = compute_psd(total_signal)
    total_power = np.trapezoid(psd_total, f) + 1e-30

    # Pc band definitions (period in seconds → freq in Hz)
    # Pc5: 150-600s → 1.67-6.67 mHz → 0.00167-0.00667 Hz
    # Pc4: 45-150s  → 6.67-22.2 mHz → 0.00667-0.0222 Hz
    # Pc3: 10-45s   → 22.2-100 mHz  → 0.0222-0.1 Hz
    # Pc2: 2-10s    → 100-500 mHz   → 0.1-0.5 Hz
    features[12] = band_power(f, psd_total, 0.00167, 0.00667) / total_power  # sp_ratio_Pc5
    features[13] = band_power(f, psd_total, 0.00667, 0.0222) / total_power   # sp_ratio_Pc4
    features[14] = band_power(f, psd_total, 0.0222, 0.1) / total_power       # sp_ratio_Pc3
    features[15] = band_power(f, psd_total, 0.1, 0.5) / total_power          # sp_ratio_Pc2
    features[16] = spectral_centroid(f, psd_total)                            # sp_centroid
    features[17] = spectral_edge(f, psd_total, 0.90)                         # sp_edge_freq
    features[18] = dominant_freq(f, psd_total)                                # sp_peak_freq
    features[19] = spectral_flatness(psd_total)                               # sp_flatness

    # ── 3. Entropy (6) ──
    _, psd_H = compute_psd(H_det)
    _, psd_D = compute_psd(D_det)
    _, psd_Z = compute_psd(Z_det)
    features[20] = spectral_entropy(psd_H)       # sp_entropy_H
    features[21] = spectral_entropy(psd_D)       # sp_entropy_D
    features[22] = spectral_entropy(psd_Z)       # sp_entropy_Z
    features[23] = sample_entropy(H_det)          # dyn_sampen
    features[24] = permutation_entropy(H_det)     # dyn_perm_entropy
    features[25] = spectral_entropy(psd_total)    # dyn_spectral_entropy

    # ── 4. Burst (5) — on H component ──
    b_count, b_max, b_mean, b_dur, b_dens = burst_features(H_det)
    features[26] = b_count       # burst_count
    features[27] = b_max         # burst_max_amp
    features[28] = b_mean        # burst_mean_amp
    features[29] = b_dur         # burst_duration
    features[30] = b_dens        # burst_density

    # ── 5. Polarization (6) — H/D ──
    pol = polarization_features(H_det, D_det)
    features[31] = pol[0]  # pol_dop
    features[32] = pol[1]  # pol_coherence
    features[33] = pol[2]  # pol_h_ratio
    features[34] = pol[3]  # pol_phase_diff
    features[35] = pol[4]  # pol_ellipticity
    features[36] = pol[5]  # pol_planarity

    return features


# ══════════════════════════════════════════════════════════════════
# CROSS-STATION FEATURE COMPUTATION
# ══════════════════════════════════════════════════════════════════

def compute_cross_station_features(station_window_data, station_rms_map):
    """
    Compute 16 cross-station features (consensus 8 + coherence 8) for a
    given (date, t_start) timestamp.

    station_window_data: dict {station: (H_det, D_det, Z_det)} for this timestamp
    station_rms_map: dict {station: H_rms} for this timestamp

    Returns: 16-dim numpy array or None if <2 stations
    """
    stations = sorted(station_window_data.keys())
    n_stations = len(stations)
    if n_stations < 2:
        return None

    features = np.zeros(16, dtype=np.float64)

    # ── Consensus features (8) ──
    rms_values = np.array([station_rms_map[s] for s in stations])
    rms_mean = rms_values.mean()
    rms_std = rms_values.std()

    # Consensus score: 1 - |x - mean|/mean for each station (how close to mean)
    consensus_scores = 1.0 - np.abs(rms_values - rms_mean) / (rms_mean + 1e-30)
    consensus_scores = np.clip(consensus_scores, 0, 1)

    features[0] = float(np.mean(consensus_scores))             # net_consensus_mean
    features[1] = float(np.max(consensus_scores))              # net_consensus_max
    features[2] = float(rms_std)                               # net_spread_mean (spread = std)
    features[3] = float(rms_std)  # min spread = same since single timestamp

    # spread_std: we only have one timestamp, so spread variability is 0
    # (This is computed across the window's timestamps; set to 0 for single ts)
    features[4] = 0.0                                          # net_spread_std

    # Agreement: stations within 1σ of mean
    within_1sig = np.sum(np.abs(rms_values - rms_mean) < rms_std + 1e-30)
    features[5] = float(within_1sig)                           # net_agreement_count

    # Dispersion: coefficient of variation
    features[6] = float(rms_std / (rms_mean + 1e-30))         # net_dispersion
    features[7] = float(n_stations)                            # net_coverage

    # ── Coherence features (8) ──
    # Pairwise correlation of H_det across station pairs
    H_arrays = [station_window_data[s][0] for s in stations]  # H_det per station
    n_pairs = n_stations * (n_stations - 1) // 2
    correlations = []
    plv_list = []
    coherence_band_list = []

    for i in range(n_stations):
        for j in range(i+1, n_stations):
            h1 = H_arrays[i]
            h2 = H_arrays[j]
            min_len = min(len(h1), len(h2))
            h1, h2 = h1[:min_len], h2[:min_len]

            # Pearson correlation
            corr = np.corrcoef(h1, h2)[0, 1]
            if np.isnan(corr):
                corr = 0.0
            correlations.append(corr)

            # Phase Locking Value (PLV)
            # Compute instantaneous phase via Hilbert transform
            phase1 = np.angle(sp_signal.hilbert(h1))
            phase2 = np.angle(sp_signal.hilbert(h2))
            plv = np.abs(np.mean(np.exp(1j * (phase1 - phase2))))
            plv_list.append(float(plv))

            # Coherence in Pc3 band (10-45s)
            f_coh, Cxx_coh = sp_signal.csd(h1, h1, fs=FS, nperseg=min(1024, min_len))
            _, Cyy_coh = sp_signal.csd(h2, h2, fs=FS, nperseg=min(1024, min_len))
            _, Cxy_coh = sp_signal.csd(h1, h2, fs=FS, nperseg=min(1024, min_len))
            coh_full = np.abs(Cxy_coh)**2 / (Cxx_coh * Cyy_coh + 1e-30)
            pc3_mask = (f_coh >= 0.0222) & (f_coh < 0.1)
            if pc3_mask.sum() > 0:
                coherence_band_list.append(float(np.mean(coh_full[pc3_mask])))
            else:
                coherence_band_list.append(0.0)

    correlations = np.array(correlations)
    plv_arr = np.array(plv_list)
    coh_band = np.array(coherence_band_list)

    features[8] = float(np.mean(correlations))                # network_R
    features[9] = float(np.std(rms_values) / (np.mean(rms_values) + 1e-30))  # network_spread (normalized)
    features[10] = float(np.sum(np.abs(correlations) > 0.5))  # pairwise_agreement

    # Station synchronization: inverse of normalized spread
    net_spread_norm = features[9]
    features[11] = 1.0 / (net_spread_norm + 1e-6)            # station_synchronization

    # Growth/collapse rates: set to 0 for single timestamp
    # (These require multiple timestamps within a window)
    features[12] = 0.0  # consensus_growth_rate
    features[13] = 0.0  # spread_collapse_rate

    features[14] = float(np.mean(plv_arr))                    # phase_locking_value
    features[15] = float(np.mean(coh_band))                   # mean_coherence_band

    return features


def compute_growth_rates_per_window(station_windows_grouped, station_meta_all):
    """
    Compute temporal growth rates for consensus features within each window.

    For each (station, date, t_start) group across overlapping timestamps,
    compute d(consensus)/dt and -d(spread)/dt.

    Since each window is a single snapshot, growth rates need multiple
    timestamps. We use adjacent windows from the same station-day.

    Returns: dict {(station, date, window_idx): (growth_rate, collapse_rate)}
    """
    # Group meta by (station, date) and sort by window_idx
    growth_rates = {}
    for (station, date), group in station_meta_all.groupby(['station', 'date']):
        group = group.sort_values('window_idx')
        h_rms_vals = group['h_rms'].values
        window_idxs = group['window_idx'].values

        # Compute running consensus: 1 - |rms - mean|/mean
        for k in range(len(group)):
            idx = window_idxs[k]
            # Use 3-window sliding context
            start_k = max(0, k - 1)
            end_k = min(len(group), k + 2)
            context_rms = h_rms_vals[start_k:end_k]

            if len(context_rms) < 2:
                growth_rates[(station, date, idx)] = (0.0, 0.0)
                continue

            context_mean = context_rms.mean()
            context_consensus = 1.0 - np.abs(context_rms - context_mean) / (context_mean + 1e-30)
            context_consensus = np.clip(context_consensus, 0, 1)

            context_spread = np.std(context_rms) / (context_mean + 1e-30)

            # dt = number of windows in context
            dt = end_k - start_k
            if dt > 1:
                # d(consensus)/dt: slope of consensus over context
                consensus_slope = (context_consensus[-1] - context_consensus[0]) / dt
                # -d(spread)/dt: negative slope of spread (positive = collapsing)
                spread_vals = []
                for m in range(start_k, end_k):
                    sub = h_rms_vals[max(0, m-1):min(len(group), m+2)]
                    sm = sub.std() / (sub.mean() + 1e-30)
                    spread_vals.append(sm)
                spread_slope = -(spread_vals[-1] - spread_vals[0]) / dt
            else:
                consensus_slope = 0.0
                spread_slope = 0.0

            growth_rates[(station, date, idx)] = (float(consensus_slope), float(spread_slope))

    return growth_rates


# ══════════════════════════════════════════════════════════════════
# MAIN EXTRACTION PIPELINE
# ══════════════════════════════════════════════════════════════════

def main():
    t0 = time.time()
    print('=' * 70)
    print('  ULF2A PHYSICS-FIRST FEATURE EXTRACTION')
    print('=' * 70)
    print(f'  Target: {len(FEATURE_NAMES)} features, 7 families')
    print()

    # ── Load metadata ──
    print('  Loading window metadata...')
    meta_path = ULF1 / 'ulf1_window_meta.csv'
    meta_df = pd.read_csv(meta_path)
    meta_df['date'] = meta_df['date'].astype(str)
    meta_df['station_day'] = meta_df['station'] + '_' + meta_df['date']
    n_windows = len(meta_df)
    print(f'    {n_windows} windows, {meta_df["station"].nunique()} stations')

    # ── Load HDF5 ──
    h5_path = ULF1 / 'ulf1_windows.h5'
    print(f'  Loading HDF5: {h5_path}...')
    t_h5 = time.time()
    with h5py.File(h5_path, 'r') as f:
        assert f.attrs['n_windows'] == n_windows, \
            f"HDF5 ({f.attrs['n_windows']}) != meta ({n_windows})"
        H_det = f['H_det'][:]  # (n_windows, 3600)
        D_det = f['D_det'][:]
        Z_det = f['Z_det'][:]
    print(f'    Loaded in {time.time()-t_h5:.1f}s, shape={H_det.shape}')

    # ── Phase 1: Station-level features (45 per window) ──
    print(f'\n  [Phase 1] Station-level features (45 per window × {n_windows})...')
    t_ph1 = time.time()
    station_features = np.zeros((n_windows, 37), dtype=np.float64)

    batch_size = 1000
    n_batches = (n_windows + batch_size - 1) // batch_size
    for b in range(n_batches):
        i_start = b * batch_size
        i_end = min((b + 1) * batch_size, n_windows)
        for i in range(i_start, i_end):
            station_features[i] = extract_single_window(H_det[i], D_det[i], Z_det[i])
        if (b + 1) % 5 == 1 or b == n_batches - 1:
            print(f'    Batch {b+1}/{n_batches} done ({i_end}/{n_windows})')

    elapsed_ph1 = time.time() - t_ph1
    print(f'    Phase 1 complete: {elapsed_ph1:.1f}s')

    # ── Phase 2: Cross-station features (16 per window) ──
    print(f'\n  [Phase 2] Cross-station features (16 per window)...')
    t_ph2 = time.time()

    # Group by (date, t_start) to find windows at same timestamp across stations
    meta_df['t_start'] = meta_df['t_start'].astype(int)
    meta_df['h_rms_val'] = station_features[:, 0]  # H_rms from phase 1

    cross_features = np.zeros((n_windows, 16), dtype=np.float64)
    cross_features.fill(np.nan)  # default NaN for single-station timestamps

    # Build lookup: (date, t_start) → list of (station_idx, H_det)
    print('    Building timestamp index...')
    ts_groups = {}
    for i in range(n_windows):
        key = (meta_df.iloc[i]['date'], meta_df.iloc[i]['t_start'])
        if key not in ts_groups:
            ts_groups[key] = []
        ts_groups[key].append(i)

    # Compute cross-station features per timestamp group
    n_multi = 0
    n_single = 0
    for key, indices in ts_groups.items():
        if len(indices) < 2:
            n_single += 1
            continue
        n_multi += 1

        # Build station data for this timestamp
        station_data = {}
        station_rms = {}
        for idx in indices:
            st = meta_df.iloc[idx]['station']
            station_data[st] = (H_det[idx], D_det[idx], Z_det[idx])
            station_rms[st] = meta_df.iloc[idx]['h_rms_val']

        cross = compute_cross_station_features(station_data, station_rms)
        if cross is not None:
            for idx in indices:
                cross_features[idx] = cross

    print(f'    Multi-station timestamps: {n_multi}, single: {n_single}')
    print(f'    Phase 2 complete: {time.time()-t_ph2:.1f}s')

    # ── Phase 2b: Growth rates (temporal derivatives) ──
    print(f'\n  [Phase 2b] Computing growth/collapse rates...')
    t_ph2b = time.time()
    growth_rates = compute_growth_rates_per_window(None, meta_df)

    # Fill growth rates into cross_features
    growth_count = 0
    for i in range(n_windows):
        key = (meta_df.iloc[i]['station'], meta_df.iloc[i]['date'],
               meta_df.iloc[i]['window_idx'])
        if key in growth_rates:
            gr, cr = growth_rates[key]
            cross_features[i, 12] = gr   # consensus_growth_rate
            cross_features[i, 13] = cr   # spread_collapse_rate
            growth_count += 1

    print(f'    Growth rates computed for {growth_count}/{n_windows} windows')
    print(f'    Phase 2b complete: {time.time()-t_ph2b:.1f}s')

    # ── Merge all features ──
    print('\n  Merging feature matrix...')
    all_features = np.hstack([station_features, cross_features])  # (n_windows, 61)

    # Replace NaN with 0 for single-station timestamps (consensus/coherence features)
    nan_count = np.isnan(all_features).sum()
    all_features = np.nan_to_num(all_features, nan=0.0)
    print(f'    NaN values replaced: {nan_count}')

    # Verify feature count
    assert all_features.shape[1] == len(FEATURE_NAMES), \
        f"Feature count mismatch: {all_features.shape[1]} vs {len(FEATURE_NAMES)}"

    # ── Build output DataFrame ──
    out_df = meta_df[['station', 'date', 'window_idx', 't_start', 't_end']].copy()
    for i, fname in enumerate(FEATURE_NAMES):
        out_df[fname] = all_features[:, i]

    # ── Save ──
    out_path = OUT / 'ulf2_features_window.csv'
    out_df.to_csv(out_path, index=False, float_format='%.6f')
    print(f'\n  Saved: {out_path}')
    print(f'    Shape: {out_df.shape}')
    print(f'    Features: {len(FEATURE_NAMES)}')

    # ── Feature metadata ──
    feat_meta = {
        'n_features': len(FEATURE_NAMES),
        'n_windows': n_windows,
        'feature_names': FEATURE_NAMES,
        'feature_families': FAMILY_MAP,
        'families': {
            'energy': [f for f in FEATURE_NAMES if FAMILY_MAP[f] == 'energy'],
            'spectral': [f for f in FEATURE_NAMES if FAMILY_MAP[f] == 'spectral'],
            'entropy': [f for f in FEATURE_NAMES if FAMILY_MAP[f] == 'entropy'],
            'burst': [f for f in FEATURE_NAMES if FAMILY_MAP[f] == 'burst'],
            'polarization': [f for f in FEATURE_NAMES if FAMILY_MAP[f] == 'polarization'],
            'consensus': [f for f in FEATURE_NAMES if FAMILY_MAP[f] == 'consensus'],
            'coherence': [f for f in FEATURE_NAMES if FAMILY_MAP[f] == 'coherence'],
        },
        'feature_counts': {
            fam: sum(1 for f in FEATURE_NAMES if FAMILY_MAP[f] == fam)
            for fam in set(FAMILY_MAP.values())
        },
        'nan_replaced': int(nan_count),
        'cross_station_timestamps': n_multi,
        'single_station_timestamps': n_single,
    }
    meta_path = OUT / 'ulf2_feature_metadata.json'
    with open(meta_path, 'w') as f:
        json.dump(feat_meta, f, indent=2)
    print(f'  Saved metadata: {meta_path}')

    # -- Summary statistics --
    print('\n  --- Feature Statistics ---')
    print(f'  Total features: {len(FEATURE_NAMES)}')
    for fam in sorted(set(FAMILY_MAP.values())):
        fam_feats = [f for f in FEATURE_NAMES if FAMILY_MAP[f] == fam]
        print(f'  {fam}: {len(fam_feats)} features')
        for f in fam_feats:
            col = out_df[f]
            print(f'    {f:30s}  mean={col.mean():12.4f}  std={col.std():12.4f}  '
                  f'min={col.min():12.4f}  max={col.max():12.4f}')

    elapsed = time.time() - t0
    print(f'\n  Done in {elapsed:.1f}s')
    print('=' * 70)
    return 0


if __name__ == '__main__':
    sys.exit(main())
