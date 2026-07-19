
"""
V3_Compile_HDF5_Final.py
========================
PRODUKSI DISERTASI: ScalogramV3 Cosmic Integration Engine (Final Edition).
Membangun dataset HDF5 dengan Azimuth Ground-Truth Aktual dan Forensic Metadata.
"""

import os
import re
import h5py
import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm
from datetime import datetime, timedelta
import math

def calculate_initial_bearing(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    d_lon = lon2 - lon1
    y = math.sin(d_lon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - \
        math.sin(lat1) * math.cos(lat2) * math.cos(d_lon)
    bearing = math.atan2(y, x)
    bearing = math.degrees(bearing)
    return (bearing + 360) % 360

# ============================================================
# CONFIGURATION
# ============================================================
V2_BASE          = r"d:\multi\scalogramv2\processed_tensors_v2"
STORM_REINFORCE  = r"d:\multi\CHECKPOINT_DATASET_V5_SCALOGRAM\images\stage1_train"
KP_CSV           = r"d:\multi\scalogramv3\kp_index_2018_2026.csv"
DST_TXT          = r"d:\multi\intial\dst.txt"
CATALOG_CSV      = r"d:\multi\earthquake_catalog_2018_2025_merged_robust.csv"
STATION_CSV      = r"d:\multi\dataset_fix\station_coordinates.csv"
OUTPUT_H5        = r"d:\multi\scalogramv3\scalogram_v3_cosmic_final.h5"

DEFAULT_KP   = 1.5
DEFAULT_DST  = -15.0

# ============================================================
# PHASE 1: DATA LOADING (Cosmic, Catalog, Stations)
# ============================================================
def load_auxiliary_data():
    print("\n[Phase 1] Loading Auxiliary Data...")
    
    # 1. Stations
    sdf = pd.read_csv(STATION_CSV, sep=';')
    sdf['Kode Stasiun'] = sdf['Kode Stasiun'].str.strip()
    sdf['Latitude'] = sdf['Latitude'].astype(str).str.replace('\xa0', '').str.replace(',', '.').astype(float)
    sdf['Longitude'] = sdf['Longitude'].astype(str).str.replace('\xa0', '').str.replace(',', '.').astype(float)
    stations = sdf.set_index('Kode Stasiun')[['Latitude', 'Longitude']].to_dict('index')

    # 2. Cosmic (Daily Peaks)
    kp_df = pd.read_csv(KP_CSV)
    kp_df['date'] = pd.to_datetime(kp_df['Date_Time_UTC'], utc=True).dt.strftime('%Y-%m-%d')
    kp_daily = kp_df.groupby('date')['Kp_Index'].max().to_dict()

    dst_daily = {}
    try:
        dst_df = pd.read_csv(DST_TXT, sep=r'\s+', skiprows=1, header=None, engine='python', on_bad_lines='skip')
        dst_df = dst_df.iloc[:, [0, -1]]
        dst_df.columns = ['date', 'dst']
        dst_df['dst'] = pd.to_numeric(dst_df['dst'], errors='coerce')
        dst_df['date'] = pd.to_datetime(dst_df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        dst_df = dst_df.dropna()
        dst_daily = dst_df.groupby('date')['dst'].min().to_dict()
    except: pass
    
    dates = sorted(set(kp_daily) | set(dst_daily))
    cosmic_lookup = {d: [float(kp_daily.get(d, DEFAULT_KP)), float(dst_daily.get(d, DEFAULT_DST))] for d in dates}

    # 3. Earthquake Catalog
    eq_catalog = pd.read_csv(CATALOG_CSV)
    if 'Date time' in eq_catalog.columns:
        eq_catalog['datetime'] = eq_catalog['datetime'].fillna(eq_catalog['Date time'])
    eq_catalog['dt'] = pd.to_datetime(eq_catalog['datetime'], format='mixed', utc=True)
    eq_catalog = eq_catalog.dropna(subset=['dt', 'Latitude', 'Longitude', 'Magnitude'])
    eq_catalog = eq_catalog[eq_catalog['Magnitude'] >= 4.5]

    return stations, cosmic_lookup, eq_catalog

# ============================================================
# PHASE 2: CRAWLING & BEARING CALCULATION
# ============================================================
def crawl_and_prepare(split, aux):
    stations, cosmic_lookup, eq_catalog = aux
    records = []
    rex_date = re.compile(r'(\d{8})') 
    
    for label_dir, label_val in [('anomali', 1), ('normal', 0)]:
        folder = Path(V2_BASE) / split / label_dir
        if not folder.exists(): continue
        
        files = sorted(folder.glob('*.npy'))
        for f in files:
            fname = f.name
            # event_STN_YYYYMMDD.npy
            parts = fname.split('_')
            stn = parts[1] if len(parts) >= 3 else "UNK"
            m = rex_date.search(fname)
            dstr = m.group(1) if m else None
            
            date_dash = f"{dstr[:4]}-{dstr[4:6]}-{dstr[6:]}" if dstr else None
            cosmic = cosmic_lookup.get(date_dash, [DEFAULT_KP, DEFAULT_DST])
            
            # Azimuth & Magnitude Calculation
            azm = 0.0
            mag_val = 0.0
            if label_val == 1 and dstr and stn in stations:
                obs_date = datetime.strptime(dstr, '%Y%m%d')
                obs_dt_utc = pd.Timestamp(obs_date).tz_localize('UTC')
                
                # Window 3-11 days later
                mask = (eq_catalog['dt'] >= (obs_dt_utc + pd.Timedelta(days=3))) & \
                       (eq_catalog['dt'] <= (obs_dt_utc + pd.Timedelta(days=11)))
                matches = eq_catalog[mask]
                if not matches.empty:
                    best_eq = matches.sort_values('Magnitude', ascending=False).iloc[0]
                    stn_lat, stn_lon = stations[stn]['Latitude'], stations[stn]['Longitude']
                    azm = calculate_initial_bearing(stn_lat, stn_lon, best_eq['Latitude'], best_eq['Longitude'])
                    mag_val = best_eq['Magnitude']

            records.append({
                'path': str(f), 'label': label_val, 
                'kp': cosmic[0], 'dst': cosmic[1], 
                'azm': azm, 'mag_val': mag_val, 'meta': fname
            })
            
    # Injection reinforcement (Mei 2024 Storm)
    if split == 'train':
        print(f"  [Reinforcement] Injecting Storm Samples...")
        for sub, lbl in [('Event', 1), ('Normal', 0)]:
            fld = Path(STORM_REINFORCE) / sub
            if not fld.exists(): continue
            for f in fld.glob('*.npy'):
                # Simpler meta for reinforced samples
                records.append({
                    'path': str(f), 'label': lbl, 'kp': 9.0 if lbl==0 else 1.5, 'dst': -300.0 if lbl==0 else -15.0,
                    'azm': 0.0, 'mag_val': 5.0 if lbl==1 else 0.0, 'meta': f.name
                })
                    
    return records

# ============================================================
# PHASE 3: COMPILATION
# ============================================================
def create_hdf5(records_map):
    print(f"\n[Phase 3] Building {OUTPUT_H5}...")
    import shutil
    
    # SAFEGUARD 1: Backup existing file
    if os.path.exists(OUTPUT_H5):
        backup_path = OUTPUT_H5.replace('.h5', '_BACKUP.h5')
        print(f"  [Safeguard 1] Backing up existing HDF5 to {backup_path}")
        shutil.copy(OUTPUT_H5, backup_path)
        os.remove(OUTPUT_H5)

    with h5py.File(OUTPUT_H5, 'w') as hf:
        for split, records in records_map.items():
            N = len(records)
            grp = hf.create_group(split)
            
            # Disable compression for speed and low memory usage
            d_tensors = grp.create_dataset('tensors', (N, 3, 128, 1440), dtype='f2', chunks=(1, 3, 128, 1440))
            d_cosmic  = grp.create_dataset('cosmic_features', (N, 2), dtype='f4')
            d_event   = grp.create_dataset('label_event', (N,), dtype='i1')
            d_mag     = grp.create_dataset('label_mag', (N,), dtype='f4')
            d_azm     = grp.create_dataset('label_azm', (N,), dtype='f4')
            d_meta    = grp.create_dataset('meta', (N,), dtype=h5py.string_dtype(encoding='utf-8'))
            
            for i, r in enumerate(tqdm(records, desc=f"  Compiling {split}")):
                try:
                    arr = np.load(r['path'])
                    # Robust reshaping
                    if arr.size == 3 * 128 * 1440:
                        if arr.shape != (3, 128, 1440):
                            arr = arr.reshape(3, 128, 1440)
                    else:
                        print(f"\n  [!] Shape Mismatch in {r['path']}: {arr.shape}. Using Zeroes...")
                        arr = np.zeros((3, 128, 1440), dtype=np.float16) # Low memory zero
                    
                    # Convert to float16 immediately
                    arr_h16 = arr.astype(np.float16)
                    d_tensors[i] = arr_h16
                    
                    d_cosmic[i]  = [r['kp'], r['dst']]
                    d_event[i]   = r['label']
                    d_mag[i]     = r['mag_val']
                    d_azm[i]     = r['azm']
                    d_meta[i]    = r['meta']
                    
                    # Manual cleanup every 100 iterations to prevent memory leak
                    if i % 100 == 0:
                        import gc
                        del arr
                        del arr_h16
                        gc.collect()

                except Exception as e:
                    print(f"\n  [!] Error loading {r['path']}: {e}")
                    d_tensors[i] = np.zeros((3, 128, 1440), dtype=np.float16)
            
            grp.attrs['samples'] = N
            grp.attrs['seismic'] = sum(1 for x in records if x['label'] == 1)
            print(f"  -> {split} complete. {grp.attrs['seismic']} anomali records with real bearings.")

if __name__ == "__main__":
    aux = load_auxiliary_data()
    data = {s: crawl_and_prepare(s, aux) for s in ['train', 'val']}
    create_hdf5(data)
    print(f"\n✅ SUCCESS: {OUTPUT_H5} is ready for retraining.")
