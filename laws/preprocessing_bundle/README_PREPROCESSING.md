# ScalogramV3 V8 Preprocessing Bundle

**Purpose:** Transform raw geomagnetic magnetometer data (H, D, Z components) into production-ready tensors compatible with `MultiTaskScalogramV3_v8`.

**Target Tensor Shape:** `(3, 128, 1440)`

---

## QUICK START

### Installation

```bash
pip install -r requirements_preprocessing.txt
```

### Basic Usage

```python
from core.signal_processing import GeomagneticSignalProcessor
from tensor_generation.v2_tensor_generator import V2TensorGenerator
from core.polarization import compute_polarization, mad_norm
import numpy as np

# 1. Load raw H,D,Z data (1 Hz, 86400 samples for 1 day)
h_raw = np.load('h_data.npy')  # Shape: (86400,)
d_raw = np.load('d_data.npy')  # Shape: (86400,)
z_raw = np.load('z_data.npy')  # Shape: (86400,)

# 2. Signal processing (gap handling + PC3 filtering)
processor = GeomagneticSignalProcessor(sampling_rate=1.0)
processed = processor.process_components(h_raw, d_raw, z_raw, apply_pc3=True)

# 3. Generate CWT scalogram tensor
generator = V2TensorGenerator()
tensor, _ = generator.generate_tensor(
    processed['h_pc3'], 
    processed['d_pc3'], 
    processed['z_pc3']
)
# tensor shape: (3, 128, 1440)

# 4. Z-score normalization
tensor_norm = generator.zscore_normalize(tensor)

# 5. (Optional) Polarization feature engineering for V3
import torch
tensor_torch = torch.from_numpy(tensor_norm).float()
h_chan = tensor_torch[0]
z_chan = tensor_torch[2]
tensor_final = compute_polarization(h_chan, z_chan, quantile=0.995)
tensor_final = mad_norm(tensor_final)  # Optional MAD normalization

print(f"Final tensor shape: {tensor_final.shape}")  # (3, 128, 1440)
```

---

## BUNDLE STRUCTURE

```
preprocessing_bundle/
├── README_PREPROCESSING.md          # This file
├── requirements_preprocessing.txt   # Python dependencies
├── config.yaml                      # Configuration parameters
├── core/                            # Core preprocessing modules
│   ├── signal_processing.py         # GeomagneticSignalProcessor (PC3 filtering)
│   ├── polarization.py              # Polarization feature engineering
│   └── __init__.py
├── data_fetching/                   # Raw data fetching
│   ├── geomagnetic_fetcher.py       # SSH/local data fetcher
│   ├── read_mdata.py                # BMKG binary parser
│   └── __init__.py
├── tensor_generation/               # CWT scalogram generation
│   ├── v2_tensor_generator.py       # V2TensorGenerator (CWT + pooling)
│   └── __init__.py
├── data_loading/                    # HDF5 data loading
│   ├── v3_dataloader.py             # GeomagneticCosmicDataset
│   └── __init__.py
└── assets/                          # Runtime data files
    └── cosmic_features_v3.csv      # Kp and Dst indices
```

---

## PREPROCESSING PIPELINE STAGES

### Stage 1: Signal Processing (`core/signal_processing.py`)

**Class:** `GeomagneticSignalProcessor`

**Operations:**
- Gap handling (interpolation for gaps < 60s, zero-padding for larger gaps)
- PC3 bandpass filtering (22-100 mHz)
- Z/H ratio calculation

**Parameters:**
- Sampling rate: 1.0 Hz
- PC3 low frequency: 0.022 Hz
- PC3 high frequency: 0.1 Hz
- Filter order: 4

**Output:** Filtered H, D, Z components (86400 samples each)

---

### Stage 2: CWT Scalogram Generation (`tensor_generation/v2_tensor_generator.py`)

**Class:** `V2TensorGenerator`

**Operations:**
- Temporal pooling (60-second mean averaging): 86400 → 1440 time steps
- Continuous Wavelet Transform (CWT) with `cmor1.5-1.0` wavelet
- Magnitude extraction from complex coefficients
- Z-score normalization (per channel)

**Parameters:**
- Wavelet: `cmor1.5-1.0` (Complex Morlet)
- Frequency range: 0.0005 Hz to 0.1 Hz (Pc5 to Pc3 bands)
- Frequency bins: 128 (logarithmic spacing)
- Pool size: 60 seconds

**Output:** Tensor shape `(3, 128, 1440)`

---

### Stage 3: Polarization Feature Engineering (`core/polarization.py`)

**Functions:** `compute_polarization`, `mad_norm`

**Operations:**
- Compute Z/H ratio with adaptive clipping
- Log1p transform for numerical stability
- Stack: `[H, Z, log1p(clipped_ratio)]`
- Optional MAD (Median Absolute Deviation) normalization

**Parameters:**
- Clipping quantile: 0.995
- Epsilon: 1e-6

**Output:** Polarization-enhanced tensor `(3, 128, 1440)`

---

### Stage 4: Cosmic Features Injection (`data_loading/v3_dataloader.py`)

**Class:** `GeomagneticCosmicDataset`

**Operations:**
- Load Kp and Dst indices from `assets/cosmic_features_v3.csv`
- Bounded normalization:
  - Kp: divide by 9.0 (range 0-1)
  - Dst: `tanh(Dst/50.0)` (range -1 to 1)

**Output:** Cosmic vector `[Kp_norm, Dst_tanh]`

---

## CONFIGURATION

Edit `config.yaml` to adjust parameters:

```yaml
data:
  tensor_shape: [3, 128, 1440]
  freq_bins: 128
  time_steps: 1440
  ulf_band_bins: [0, 95]  # 0.001 - 0.1 Hz
```

---

## DATA FETCHING

### Option 1: Local Data Archives

Use `data_fetching/read_mdata.py` to parse BMKG binary format:

```python
from data_fetching.read_mdata import read_604rcsv_new_python

data = read_604rcsv_new_python(2023, 1, 1, 'SCN', '/path/to/mdata')
# Returns dict with H, D, Z, X, Y, etc.
```

### Option 2: Remote SSH Fetching

Use `data_fetching/geomagnetic_fetcher.py` for SSH access:

```python
from data_fetching.geomagnetic_fetcher import GeomagneticDataFetcher

with GeomagneticDataFetcher() as fetcher:
    data = fetcher.fetch_data(datetime(2023, 1, 1), 'SCN')
```

**Note:** SSH credentials are hardcoded in `geomagnetic_fetcher.py`. For production, implement secure credential management.

---

## DEPENDENCIES

### Required
- `numpy>=1.23.0` - Numerical computing
- `scipy>=1.9.0` - Signal processing (Butterworth filters)
- `PyWavelets>=1.4.0` - CWT implementation
- `pandas>=1.5.0` - CSV handling
- `h5py>=3.7.0` - HDF5 I/O
- `tqdm>=4.64.0` - Progress bars

### Optional
- `paramiko>=2.11.0` - SSH data fetching
- `torch>=1.13.0` - Polarization features (PyTorch)
- `scikit-learn>=1.1.0` - ML utilities

---

## EXAMPLE WORKFLOWS

### Workflow 1: Minimal Tensor Generation

```python
from tensor_generation.v2_tensor_generator import generate_tensor_from_raw
import numpy as np

# Assuming data is already PC3-filtered
h_filtered = np.load('h_filtered.npy')
d_filtered = np.load('d_filtered.npy')
z_filtered = np.load('z_filtered.npy')

tensor = generate_tensor_from_raw(h_filtered, d_filtered, z_filtered)
print(tensor.shape)  # (3, 128, 1440)
```

### Workflow 2: Full Pipeline with Data Fetching

```python
from data_fetching.geomagnetic_fetcher import GeomagneticDataFetcher
from core.signal_processing import GeomagneticSignalProcessor
from tensor_generation.v2_tensor_generator import V2TensorGenerator
from datetime import datetime

# Fetch raw data
with GeomagneticDataFetcher() as fetcher:
    raw_data = fetcher.fetch_data(datetime(2023, 1, 1), 'SCN')

# Signal processing
processor = GeomagneticSignalProcessor()
processed = processor.process_components(
    raw_data['Hcomp'], 
    raw_data['Dcomp'], 
    raw_data['Zcomp']
)

# Generate tensor
generator = V2TensorGenerator()
tensor, _ = generator.generate_tensor(
    processed['h_pc3'], 
    processed['d_pc3'], 
    processed['z_pc3']
)

# Normalize
tensor_norm = generator.zscore_normalize(tensor)
```

### Workflow 3: HDF5 Dataset Creation

```python
from data_loading.v3_dataloader import GeomagneticCosmicDataset
import h5py

# Create HDF5 file
with h5py.File('output.h5', 'w') as hf:
    grp = hf.create_group('train')
    d_tensors = grp.create_dataset('tensors', (N, 3, 128, 1440), dtype='f2')
    d_cosmic = grp.create_dataset('cosmic_features', (N, 2), dtype='f4')
    
    for i in range(N):
        tensor = generate_tensor_from_raw(...)
        d_tensors[i] = tensor.astype(np.float16)
        d_cosmic[i] = [kp_norm, dst_norm]
```

---

## TESTING

Run the built-in test for `V2TensorGenerator`:

```bash
cd preprocessing_bundle/tensor_generation
python v2_tensor_generator.py
```

Expected output:
```
Testing V2TensorGenerator with synthetic data...
Generated tensor shape: (3, 128, 1440)
Expected shape: (3, 128, ~1440)
Actual time steps: 1440
Normalized tensor mean: 0.000000
Normalized tensor std: 1.000000

✓ V2TensorGenerator test passed
```

---

## TROUBLESHOOTING

### Issue: `ImportError: No module named 'pywt'`

**Solution:** Install PyWavelets
```bash
pip install PyWavelets>=1.4.0
```

### Issue: Tensor shape mismatch

**Solution:** Ensure input data is at 1 Hz sampling rate with 86400 samples (24 hours). The pooling will automatically adjust to 1440 time steps.

### Issue: SSH connection fails

**Solution:** Check network connectivity and credentials in `data_fetching/geomagnetic_fetcher.py`. For production, use local data archives instead.

### Issue: Polarization features produce NaN

**Solution:** Ensure H component is not zero. The polarization computation uses `Z / (H + eps)` with `eps=1e-6` to prevent division by zero.

---

## NOTES FOR ENGINEERS

### V2 vs V3 Separation

The original codebase has V2 and V3 workspaces:
- **V2**: CWT scalogram generation, temporal pooling, Z-score normalization
- **V3**: Signal processing, polarization features, cosmic features

This bundle combines both stages into a single deployable package.

### Data Format Requirements

- **Sampling rate:** 1 Hz (1 sample per second)
- **Duration:** 24 hours (86400 samples) for standard daily tensors
- **Components:** H (horizontal), D (declination), Z (vertical)
- **Binary format:** BMKG .STN or .gz format (use `read_mdata.py`)

### Quality Control

- Gaps > 60 seconds are zero-padded (not interpolated)
- Binary mask propagation ensures data quality flags are preserved
- Adaptive clipping prevents outliers in polarization features

---

## SUPPORT

For detailed technical documentation, see `PREPROCESSING_DEPLOYMENT_REPORT.md` in the parent directory.

---

**Version:** 1.0
**Last Updated:** 2025-01-18
**Compatible with:** ScalogramV3 V8 (MultiTaskScalogramV3_v8)
