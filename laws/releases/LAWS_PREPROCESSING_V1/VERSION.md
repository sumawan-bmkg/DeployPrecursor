LAWS PREPROCESSING

Version : 1.0

Status:
Frozen

Input

BMKG binary (.ALR)

Reader

read_mdata.py

Signal processing

signal_processing.py

Filter

PC3 Butterworth

Pooling

60 second mean

Wavelet

cmor1.5-1.0

Frequency

0.0005-0.1 Hz

Output

Tensor

Shape

(3,128,1440)

Normalization

Per-channel Z-score

Compiler

V3_Compile_HDF5_Final.py

Target

Operational Dataset
