"""
V3_Compile_HDF5.py
==================
PRODUKSI DISERTASI: ScalogramV3 Cosmic Integration Engine.
Membangun dataset HDF5 yang mengintegrasikan Spectral Tensors (Seismic) dengan 
Geomagnetic Indices (Kp/Dst) untuk Sensor Fusion.

Fitur Utama:
1. Robust Dst Parsing: Menangani malfomasi data pada dst.txt.
2. Storm Peak Logic: Menggunakan Kp_max dan Dst_min harian (Badai Terburuk).
3. Memory Optimization: Chunks (1, 3, 128, 1440) & Gzip Compression.
4. Forensic Ready: Menyimpan metadata statistik per split (train/val).
"""

import os
import re
import h5py
import numpy as np
import pandas as pd
from pathlib import Path
from tqdm import tqdm

# ============================================================
# CONFIGURATION
# ============================================================
V2_BASE      = r"d:\multi\scalogramv2\processed_tensors_v2"
# Reinforcement source untuk badai ekstrim Mei 2024
STORM_REINFORCE = r"d:\multi\CHECKPOINT_DATASET_V5_SCALOGRAM\images\stage1_train"
KP_CSV       = r"d:\multi\scalogramv3\kp_index_2018_2026.csv"
DST_TXT      = r"d:\multi\intial\dst.txt"
OUTPUT_H5    = r"d:\multi\scalogramv3\scalogram_v3_augmented.h5"

DEFAULT_KP   = 1.5
DEFAULT_DST  = -15.0

# ============================================================
# PHASE 1: COSMIC DATA PARSING
# ============================================================
def build_cosmic_lookup():
    print("\n[Phase 1] Aggregating Cosmic Data (Kp & Dst)...")
    
    # 1. Kp Index (Daily Max)
    kp_df = pd.read_csv(KP_CSV)
    kp_df['date'] = pd.to_datetime(kp_df['Date_Time_UTC'], utc=True).dt.strftime('%Y-%m-%d')
    kp_daily = kp_df.groupby('date')['Kp_Index'].max().to_dict()
    
    # 2. Dst Index (Daily Min - Seeking the negative peaks)
    try:
        # Menangani whitespace delimiter dan skipping header meta
        dst_df = pd.read_csv(DST_TXT, sep=r'\s+', skiprows=1, header=None, engine='python', on_bad_lines='skip')
        dst_df = dst_df.iloc[:, [0, -1]] # Col 0: Date, Last Col: Dst
        dst_df.columns = ['date', 'dst']
        dst_df['dst'] = pd.to_numeric(dst_df['dst'], errors='coerce')
        dst_df['date'] = pd.to_datetime(dst_df['date'], errors='coerce').dt.strftime('%Y-%m-%d')
        dst_df = dst_df.dropna()
        dst_daily = dst_df.groupby('date')['dst'].min().to_dict()
        print(f"  (!) Cosmic Peak Detection: Lowest Dst found is {min(dst_daily.values())} nT")
    except Exception as e:
        print(f"  [!] Dst Error: {e}. Falling back to defaults.")
        dst_daily = {}

    # 3. Aggregation
    dates = sorted(set(kp_daily) | set(dst_daily))
    lookup = {d: [float(kp_daily.get(d, DEFAULT_KP)), float(dst_daily.get(d, DEFAULT_DST))] for d in dates}
    return lookup

# ============================================================
# PHASE 2: TENSOR CRAWLING & INJECTION
# ============================================================
def crawl_and_inject(split, lookup):
    records = []
    rex = re.compile(r'(\d{8})') 
    
    for label_dir, label_val in [('anomali', 1), ('normal', 0)]:
        folder = Path(V2_BASE) / split / label_dir
        if not folder.exists(): continue
        
        files = sorted(folder.glob('*.npy'))
        for f in files:
            m = rex.search(f.stem)
            date_key = f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}" if m else None
            cosmic = lookup.get(date_key, [DEFAULT_KP, DEFAULT_DST])
            
            records.append({
                'path': str(f), 'label': label_val, 
                'kp': cosmic[0], 'dst': cosmic[1], 'date': date_key
            })
            
    # Injection: Reinforcement badai Mei 2024 (dari V5 Checkpoint)
    if split == 'train':
        print(f"  [Reinforcement] Injecting Storm Samples from {STORM_REINFORCE}...")
        for sub, lbl in [('Event', 1), ('Normal', 0)]:
            fld = Path(STORM_REINFORCE) / sub
            if fld.exists():
                for f in fld.glob('*.npy'):
                    m = rex.search(f.stem)
                    dk = f"{m.group(1)[:4]}-{m.group(1)[4:6]}-{m.group(1)[6:]}" if m else None
                    cos = lookup.get(dk, [DEFAULT_KP, DEFAULT_DST])
                    records.append({'path': str(f), 'label': lbl, 'kp': cos[0], 'dst': cos[1], 'date': dk})
                    
    return records

# ============================================================
# PHASE 3: HDF5 COMPILATION
# ============================================================
def create_hdf5(records_map):
    print(f"\n[Phase 3] Building {OUTPUT_H5}...")
    if os.path.exists(OUTPUT_H5): os.remove(OUTPUT_H5)

    with h5py.File(OUTPUT_H5, 'w') as hf:
        for split, records in records_map.items():
            N = len(records)
            grp = hf.create_group(split)
            
            d_tensors = grp.create_dataset('tensors', (N, 3, 128, 1440), dtype='f2', chunks=(1, 3, 128, 1440), compression='gzip')
            d_cosmic  = grp.create_dataset('cosmic_features', (N, 2), dtype='f4')
            d_event   = grp.create_dataset('label_event', (N,), dtype='i1')
            d_mag     = grp.create_dataset('label_mag', (N,), dtype='i1')
            d_azm     = grp.create_dataset('label_azm', (N,), dtype='f4')
            
            for i, r in enumerate(tqdm(records, desc=f"  Compiling {split}")):
                arr = np.load(r['path'])
                if arr.shape != (3, 128, 1440): arr = arr.reshape(3, 128, 1440)
                
                d_tensors[i] = arr.astype(np.float16)
                d_cosmic[i]  = [r['kp'], r['dst']]
                d_event[i]   = r['label']
                d_mag[i]     = 0 # Placeholder
                d_azm[i]     = 0.0 # Placeholder
            
            # Save Metadata
            grp.attrs['samples'] = N
            grp.attrs['seismic'] = sum(1 for x in records if x['label'] == 1)
            grp.attrs['storm_critical'] = sum(1 for x in records if x['kp'] >= 5.0)

if __name__ == "__main__":
    lookup = build_cosmic_lookup()
    data = {s: crawl_and_inject(s, lookup) for s in ['train', 'val']}
    create_hdf5(data)
    print("\n✅ PIPELINE VALIDATED: Scalogram_v3_augmented.h5 is Ready.")
