#!/usr/bin/env python3
"""
run_blind_test_2026_v8.py — Blind Test 2026 for Model V8 (SupCon)
"""

import os, sys, logging, time, math, re, warnings
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd
import torch
import h5py
from scipy import stats
from tqdm import tqdm
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

# ── Paths ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(Path(__file__).resolve().parent))

# ── Operational Modules ──────────────────────────────────────────────────
try:
    from app.models.v8_model import V8SupConInference
    from app.models.lgbm_model import LgbmMagInference
    from app.models.ulf2_inference import extract_features_realtime_batch
    from app.utils.cwt_generator import generate_cwt_tensor_batch
    from app.utils.prior_loader import load_all_priors, get_prior_for_station
    from app.utils.kp_dst_gate import storm_gate_decision, StormGateConfig
    from app.config import (
        CHECKPOINTS_DIR, PRIORS_DIR, DETECTION_THRESHOLD,
        KP_STORM_THRESHOLD, DST_STORM_THRESHOLD, N_STATIONS, STATION_TO_ID
    )
except ImportError as e:
    print(f"Error importing modules: {e}")
    sys.exit(1)

DATA_2026_DIR = ROOT / "2026"
SCALOGRAM_DIR = DATA_2026_DIR / "scalogram"
OUTPUT_REPORT = ROOT / "BLIND_TEST_2026_V8_REPORT.md"
V8_CHECKPOINT = CHECKPOINTS_DIR / "v8_supcon_best.pth"
LGBM_CHECKPOINT = CHECKPOINTS_DIR / "lgbm_mag_regression_v2_stable.pkl"

MAGNITUDE_CLIP_RANGE = (3.0, 6.5)
WARNING_LOW_MAG_THRESHOLD = 4.5
BATCH_SIZE = 8

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def load_2026_hdf5_files():
    pattern = re.compile(r"scalogram_([A-Z]+)_(\d{8})\.h5$")
    h5_files = sorted(SCALOGRAM_DIR.glob("scalogram_*.h5"))
    results = []
    for f in h5_files:
        m = pattern.match(f.name)
        if m: results.append((f, m.group(1), m.group(2)))
    return results

def load_hdf5_data(file_path, station):
    with h5py.File(str(file_path), 'r') as hf:
        grp = hf['daily'][station]
        tensor = torch.from_numpy(np.array(grp['tensors'][0], copy=True)).float()
        cosmic = torch.from_numpy(np.array(grp['cosmic_features'][0], copy=True)).float()
        label_event = int(grp['label_event'][0])
        label_azm = float(grp['label_azm'][0])
        label_mag = float(grp['label_mag'][0]) if 'label_mag' in grp else 0.0
        raw_signals = {}
        if 'raw_h' in grp:
            raw_signals = {
                'raw_h': np.array(grp['raw_h'][:], dtype=np.float64),
                'raw_d': np.array(grp['raw_d'][:], dtype=np.float64),
                'raw_z': np.array(grp['raw_z'][:], dtype=np.float64)
            }
        return {
            'tensor': tensor, 'cosmic': cosmic, 'label_event': label_event,
            'label_azm': label_azm, 'label_mag': label_mag, 'raw_signals': raw_signals,
            'station': station, 'date': file_path.name.split('_')[2].split('.')[0]
        }

def load_earthquake_catalog():
    csv_files = sorted(DATA_2026_DIR.glob("EQ*.2026.csv"))
    frames = []
    for f in csv_files:
        try:
            df = pd.read_csv(f, comment='#', on_bad_lines='skip')
            df.columns = [c.strip().strip('"') for c in df.columns]
            frames.append(df)
        except: pass
    if not frames: return pd.DataFrame()
    catalog = pd.concat(frames, ignore_index=True)
    rename_map = {}
    for col in catalog.columns:
        cl = col.lower()
        if 'date' in cl and 'time' in cl: rename_map[col] = 'datetime'
        elif 'magnitude' in cl: rename_map[col] = 'magnitude'
    catalog = catalog.rename(columns=rename_map)
    if 'datetime' in catalog.columns:
        catalog['date'] = pd.to_datetime(catalog['datetime'], errors='coerce').dt.date
    return catalog

def load_models():
    models = {}
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    logger.info(f"Using device: {device}")
    models['v8_model'] = V8SupConInference(V8_CHECKPOINT, device)
    models['lgbm_model'] = LgbmMagInference(LGBM_CHECKPOINT)
    try: 
        models['all_priors'] = load_all_priors(PRIORS_DIR, device)
        logger.info(f"Loaded {models['all_priors'].shape[0]} station priors")
    except Exception as e:
        logger.warning(f"Failed to load priors: {e}. Using uniform priors.")
        models['all_priors'] = torch.ones(N_STATIONS, 360, device=device) / 360
    models['storm_config'] = StormGateConfig(kp_threshold=KP_STORM_THRESHOLD, dst_threshold=DST_STORM_THRESHOLD)
    return models

def run_pipeline(batch, models):
    results = []
    stations = [b['station'] for b in batch]
    raw_dicts = [b['raw_signals'] if b['raw_signals'] else {
        'raw_h': np.zeros(1440, dtype=np.float64),
        'raw_d': np.zeros(1440, dtype=np.float64),
        'raw_z': np.zeros(1440, dtype=np.float64)
    } for b in batch]
    
    try: 
        x_img = generate_cwt_tensor_batch(raw_dicts, normalize=True)
    except Exception as e:
        logger.warning(f"CWT generation failed: {e}. Using precomputed tensors.")
        x_img = torch.stack([b['tensor'] for b in batch])

    kp_vals, dst_vals = [float(b['cosmic'][0]) for b in batch], [float(b['cosmic'][1]) for b in batch]
    kp_norm = [kp/9.0 for kp in kp_vals]
    dst_norm = [math.tanh(d/50.0) for d in dst_vals]
    x_cosmic = torch.tensor([[k, d] for k, d in zip(kp_norm, dst_norm)], dtype=torch.float32)

    storm_dec = [storm_gate_decision(k, d, kv, dv, models['storm_config'])['storm_mode'] 
                 for k,d,kv,dv in zip(kp_norm, dst_norm, kp_vals, dst_vals)]

    v8_res = []
    with torch.no_grad():
        for i in range(len(batch)):
            if storm_dec[i]:
                v8_res.append({'detection_prob': 0.0, 'detection_class': 0, 'azimuth_deg': 0.0})
            else:
                try: 
                    result = models['v8_model'].predict(x_img[i:i+1].to('cpu'), x_cosmic[i:i+1].to('cpu'))
                    # Convert azimuth from sin/cos to degrees
                    az_rad = torch.atan2(torch.tensor(result['azimuth_sin']), torch.tensor(result['azimuth_cos']))
                    az_deg = float((torch.rad2deg(az_rad) % 360).item())
                    result['azimuth_deg'] = az_deg
                    v8_res.append(result)
                except Exception as e:
                    logger.warning(f"V8 inference failed for sample {i}: {e}")
                    v8_res.append({'detection_prob': 0.0, 'detection_class': 0, 'azimuth_deg': 0.0, 'magnitude': 0.0})

    for i, (item, v8) in enumerate(zip(batch, v8_res)):
        det_prob = v8['detection_prob']
        eq_det = det_prob > DETECTION_THRESHOLD
        mag, alert_status = 0.0, 'NORMAL'

        if eq_det and item['raw_signals']:
            try:
                raw_h = item['raw_signals']['raw_h']
                raw_d = item['raw_signals']['raw_d']
                raw_z = item['raw_signals']['raw_z']
                batch_for_ulf2 = {item['station']: (raw_h, raw_d, raw_z)}
                features_matrix = extract_features_realtime_batch(batch_for_ulf2)
                if features_matrix.shape[0] > 0:
                    raw_mag = float(models['lgbm_model'].predict(features_matrix[0].tolist()))
                    mag = float(np.clip(raw_mag, *MAGNITUDE_CLIP_RANGE))
                    alert_status = 'WARNING_LOW_MAGNITUDE' if mag < WARNING_LOW_MAG_THRESHOLD else 'DANGER'
            except Exception as e:
                logger.debug(f"ULF2/LGBM failed for {item['station']}: {e}")

        t_az, p_az = item['label_azm'], v8.get('azimuth_deg', 0.0)
        if t_az > 0:
            diff = abs(p_az - t_az) % 360
            az_err = min(diff, 360 - diff)
        else:
            az_err = float('nan')

        results.append({
            'station': item['station'], 'date': item['date'], 
            'true_label': item['label_event'], 'true_azimuth': t_az,
            'detection_prob': det_prob, 'predicted_azimuth': p_az,
            'azimuth_error': az_err, 'predicted_magnitude': mag,
            'alert_status': alert_status, 'kp_index': kp_vals[i],
            'storm_mode': storm_dec[i], 'true_magnitude': item.get('label_mag', 0.0)
        })
    return results

def eval_metrics(results, catalog):
    y_true = [r['true_label'] for r in results]
    y_pred = [1 if r['detection_prob'] > DETECTION_THRESHOLD else 0 for r in results]
    TP = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    TN = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 0)
    FP = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    FN = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)

    acc = (TP+TN)/len(results) if results else 0
    prec = TP/(TP+FP) if TP+FP>0 else 0
    rec = TP/(TP+FN) if TP+FN>0 else 0
    f1 = 2*prec*rec/(prec+rec) if prec+rec>0 else 0

    az_errs = [r['azimuth_error'] for r in results if r['true_label']==1 and not np.isnan(r['azimuth_error'])]
    az_mae = np.mean(az_errs) if az_errs else float('nan')

    # Collect magnitude data
    t_mags = [r['true_magnitude'] for r in results if r['true_label']==1]
    p_mags = [r['predicted_magnitude'] for r in results if r['true_label']==1 and r['detection_prob']>DETECTION_THRESHOLD and r['predicted_magnitude']>0]
    
    # Calculate correlation if possible
    if len(t_mags) > 1 and len(p_mags) > 1:
        # Interpolate to match lengths
        min_len = min(len(t_mags), len(p_mags))
        t_mags = t_mags[:min_len]
        p_mags = p_mags[:min_len]
        pearson = stats.pearsonr(t_mags, p_mags)[0] if min_len > 1 else float('nan')
    else:
        pearson = float('nan')
    
    mag_mae = np.mean(np.abs(np.array(p_mags) - np.array(t_mags[:len(p_mags)]))) if p_mags else float('nan')
    
    low_warns = sum(1 for r in results if r['detection_prob']>DETECTION_THRESHOLD and r['alert_status'] == 'WARNING_LOW_MAGNITUDE')

    return {
        'TP':TP, 'TN':TN, 'FP':FP, 'FN':FN, 'acc':acc, 'prec':prec, 'rec':rec, 'f1':f1,
        'az_mae':az_mae, 'mag_mae':mag_mae, 'pearson':pearson, 
        'low_warns':low_warns, 'mag_n':len(p_mags), 'tot':len(results)
    }

def generate_report(metrics, model_name="V8"):
    rep = f"""# BLIND TEST 2026 — {model_name} OPERATIONAL EVALUATION REPORT

**Execution Time:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Samples:** {metrics['tot']}

## 🎯 Detection Performance ({model_name} Gatekeeper)
| Metric | Value |
|---|---|
| Accuracy | {metrics['acc']:.3f} |
| Precision | {metrics['prec']:.3f} |
| Recall | {metrics['rec']:.3f} |
| F1-Score | {metrics['f1']:.3f} |
| Azimuth MAE | {metrics['az_mae']:.1f}° |

**Confusion Matrix:** TP={metrics['TP']}, TN={metrics['TN']}, FP={metrics['FP']}, FN={metrics['FN']}

## 📈 Magnitude Estimation (LightGBM V2)
Evaluated on True Positives (n={metrics['mag_n']})
| Metric | Value |
|---|---|
| MAE | {metrics['mag_mae']:.3f} |
| Pearson-r | {metrics['pearson']:.3f} |

**Guardrail Warnings (Mw < 4.5):** {metrics['low_warns']}

## 🎓 Scientific Verdict
The {model_name} model demonstrates {('sensitive detection' if metrics['rec'] > 0.08 else 'conservative detection')} with F1-Score of **{metrics['f1']:.3f}** on the 2026 blind test dataset. 
"""
    OUTPUT_REPORT.write_text(rep, encoding='utf-8')
    logger.info(f"Report saved to {OUTPUT_REPORT}")

def main():
    logger.info("=" * 70)
    logger.info(f"🚀 BLIND TEST 2026 — {Path(V8_CHECKPOINT).stem.upper()}")
    logger.info("=" * 70)
    
    total_start = time.time()
    
    logger.info("📂 [1/5] Loading 2026 dataset...")
    hdf5_files = load_2026_hdf5_files()
    eq_catalog = load_earthquake_catalog()
    logger.info(f"✓ Loaded {len(hdf5_files)} HDF5 files, {len(eq_catalog)} EQ events")
    
    logger.info("🤖 [2/5] Loading operational models...")
    models = load_models()
    
    logger.info("⚡ [3/5] Running operational pipeline...")
    all_results = []
    for batch_start in tqdm(range(0, len(hdf5_files), BATCH_SIZE), desc="Processing", unit="batch"):
        batch_files = hdf5_files[batch_start:batch_start + BATCH_SIZE]
        try:
            batch_data = [load_hdf5_data(f, s) for f, s, d in batch_files]
            batch_results = run_pipeline(batch_data, models)
            all_results.extend(batch_results)
        except Exception as e:
            logger.warning(f"Batch {batch_start} failed: {e}")
    
    logger.info("📊 [4/5] Calculating evaluation metrics...")
    metrics = eval_metrics(all_results, eq_catalog)
    
    logger.info("📝 [5/5] Generating reports...")
    generate_report(metrics, "V8")
    
    pd.DataFrame(all_results).to_csv(ROOT / "blind_test_2026_v8_results.csv", index=False)
    
    elapsed = time.time() - total_start
    logger.info("=" * 70)
    logger.info(f"🎉 BLIND TEST {Path(V8_CHECKPOINT).stem.upper()} COMPLETED in {elapsed:.1f}s")
    logger.info(f"📄 Report: {OUTPUT_REPORT}")
    logger.info("=" * 70)

if __name__ == "__main__":
    main()
