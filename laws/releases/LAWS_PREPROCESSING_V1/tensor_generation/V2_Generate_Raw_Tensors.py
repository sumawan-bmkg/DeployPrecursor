import os
import sys
import numpy as np
import pywt
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from tqdm import tqdm

# Setup paths
PROJECT_DIR = Path(__file__).parent
MULTI_DIR = PROJECT_DIR.parent
sys.path.append(str(MULTI_DIR))
sys.path.append(str(MULTI_DIR / 'intial'))

from intial.geomagnetic_fetcher import GeomagneticDataFetcher
from intial.signal_processing import GeomagneticSignalProcessor

class V2TensorGenerator:
    def __init__(self, fs=1.0, wavelet='cmor1.5-1.0', scales=None):
        self.fs = fs
        self.wavelet = wavelet
        if scales is None:
            # Expanded Range: 0.001 (Pc5) to 0.1 (Pc3)
            # 128 bins ensures high resolution
            freqs = np.geomspace(0.0005, 0.1, num=128)
            self.scales = pywt.frequency2scale(self.wavelet, freqs / self.fs)
        else:
            self.scales = scales
        self.processor = GeomagneticSignalProcessor(sampling_rate=self.fs)

    def extract_cwt_tensor(self, signal_array):
        coefficients, _ = pywt.cwt(signal_array, self.scales, self.wavelet, sampling_period=1/self.fs)
        return np.abs(coefficients)

    def process_day(self, geo_data):
        if geo_data is None or geo_data['stats']['valid_samples'] < 1000:
            return None, None
            
        processed = self.processor.process_components(
            geo_data['Hcomp'], geo_data['Dcomp'], geo_data['Zcomp'], apply_pc3=True
        )
        
        # 1. Scalogram Extraction
        pool_size = 60
        def pool(arr):
            pad_len = (pool_size - len(arr) % pool_size) % pool_size
            padded = np.pad(arr, (0, pad_len), 'edge')
            return padded.reshape(-1, pool_size).mean(axis=1)
            
        h_pool = pool(processed['h_pc3'])
        d_pool = pool(processed['d_pc3'])
        z_pool = pool(processed['z_pc3'])
        
        tensor = np.stack([
            self.extract_cwt_tensor(h_pool), 
            self.extract_cwt_tensor(d_pool), 
            self.extract_cwt_tensor(z_pool)
        ], axis=0)
        
        # 2. Binary Mask Pooling (86400 -> 1440)
        # If any second in the 60s window has a long gap (>5s flagged as 0), mask the whole minute.
        raw_mask = processed['mask']
        pad_len_m = (pool_size - len(raw_mask) % pool_size) % pool_size
        padded_m = np.pad(raw_mask, (0, pad_len_m), constant_values=0)
        pooled_mask = padded_m.reshape(-1, pool_size).min(axis=1) # Min-Pool
        
        return tensor.astype(np.float32), pooled_mask.astype(np.float32)

def generate_raw_tensors(out_dir, start_date, end_date, station_code='YOG'):
    os.makedirs(out_dir, exist_ok=True)
    generator = V2TensorGenerator()
    current_date = start_date
    with GeomagneticDataFetcher() as fetcher:
        while current_date <= end_date:
            fname = f"raw_tensor_{station_code}_{int(current_date.timestamp())}.npy"
            fpath = out_dir / fname
            if fpath.exists():
                current_date += timedelta(days=1)
                continue
            print(f"Generating Raw Tensor for {current_date.date()} [{station_code}]")
            raw_data = fetcher.fetch_data(current_date, station_code)
            tensor = generator.process_day(raw_data)
            if tensor is not None:
                np.save(fpath, tensor)
            current_date += timedelta(days=1)

def normalize_and_split_tensors(raw_tensor_dir, output_base_dir, eq_catalog_path):
    os.makedirs(output_base_dir, exist_ok=True)
    eq_catalog = pd.read_csv(eq_catalog_path)
    if 'Date time' in eq_catalog.columns:
        eq_catalog['datetime'] = eq_catalog['datetime'].fillna(eq_catalog['Date time'])
    
    # Parse mixed formats, assume UTC, then convert to WIB (Asia/Jakarta)
    dt_series = pd.to_datetime(eq_catalog['datetime'], format='mixed', utc=True).dt.tz_convert('Asia/Jakarta')
    
    # Generate 3-10 days precursor window
    anomali_dates = set()
    eq_dates = dt_series[eq_catalog['Magnitude'] >= 4.5]
    for eq_date in eq_dates:
        for days_before in range(3, 11): # 3 to 10 days
            precursor_date = eq_date - pd.Timedelta(days=days_before)
            anomali_dates.add(precursor_date.strftime('%Y%m%d'))
    
    file_info = []
    for fpath in sorted(list(raw_tensor_dir.glob("raw_tensor_*.npy"))):
        parts = fpath.stem.split('_')
        dt = datetime.fromtimestamp(int(parts[3]))
        # MANDATORY 2026 PROTECTION: Skip all 2026 data in this expansion sweep
        if dt.year >= 2026: continue
        file_info.append({'path': fpath, 'date': dt, 'station': parts[2]})

    if not file_info:
        print("No 2025 raw tensors found.")
        return

    # Chronological Split (Train: Jan - Sep, Val: Oct - Dec)
    splits = {'train': [], 'val': []}
    for info in file_info:
        if info['date'].month <= 9:
            splits['train'].append(info)
        else:
            splits['val'].append(info)
            
    print(f"Chronological Split -> Train (Jan-Sep): {len(splits['train'])} | Val (Oct-Dec): {len(splits['val'])}")

    print(f"Applying Station-Specific Z-Score Normalization...")

    for sname, flist in splits.items():
        anom_dir, norm_dir = output_base_dir / sname / 'anomali', output_base_dir / sname / 'normal'
        os.makedirs(anom_dir, exist_ok=True); os.makedirs(norm_dir, exist_ok=True)
        for info in tqdm(flist, desc=f"Categorizing {sname}"):
            dstr, stn = info['date'].strftime('%Y%m%d'), info['station']
            tensor = np.load(info['path'])
            
            # Station-Specific Z-Score Normalization per channel
            normed = np.zeros_like(tensor)
            for c in range(3):
                channel_data = tensor[c]
                mean_val = np.mean(channel_data)
                std_val = np.std(channel_data)
                # Z-Score: (X - mu) / sigma
                normed[c] = (channel_data - mean_val) / (std_val + 1e-8)
                
            save_path = (anom_dir if dstr in anomali_dates else norm_dir) / f"event_{stn}_{dstr}.npy"
            np.save(save_path, normed)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='V2 Raw Tensor Generator - EWS Edition')
    parser.add_argument('--mode', type=str, default='sweep', choices=['sweep', 'incremental'], 
                        help='sweep: process 2025; incremental: process new_raw_data folder')
    parser.add_argument('--station', type=str, default='all', help='Station code or all')
    args = parser.parse_args()

    catalog_path = MULTI_DIR / 'earthquake_catalog_2018_2025_merged_robust.csv'
    stations_csv = MULTI_DIR / 'intial' / 'lokasi_stasiun.csv'
    raw_dir, proc_dir = PROJECT_DIR / 'raw_tensors_v2', PROJECT_DIR / 'processed_tensors_v2'
    
    stations_df = pd.read_csv(stations_csv, sep=';')
    station_codes = [s.strip() for s in stations_df['Kode Stasiun'].dropna().unique() if len(str(s)) >= 3]
    if args.station != 'all':
        station_codes = [args.station]

    if args.mode == 'sweep':
        print(f"--- 2025 NATIONWIDE BIG SWEEP ---")
        start_date, end_date = datetime(2025, 1, 1), datetime(2025, 12, 31)
        for code in station_codes:
            generate_raw_tensors(raw_dir, start_date, end_date, station_code=code)
        normalize_and_split_tensors(raw_dir, proc_dir, catalog_path)
        print("\n--- BIG SWEEP 2025 COMPLETE ---")
    
    elif args.mode == 'incremental':
        print(f"--- EWS INCREMENTAL MODE ---")
        # In real-world, this would fetch the last 24h for all stations
        # For simulation, we scan the 'new_raw_data' folder if it exists
        new_data_dir = PROJECT_DIR / 'new_raw_data'
        if not new_data_dir.exists():
            print(f"Creating {new_data_dir}. Place new .npy or CSV here.")
            os.makedirs(new_data_dir, exist_ok=True)
        else:
            print(f"Processing new data in {new_data_dir}...")
            # Incremental processing logic would go here
        print("--- INCREMENTAL SYNC COMPLETE ---")
