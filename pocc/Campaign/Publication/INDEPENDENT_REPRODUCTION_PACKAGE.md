# Independent Reproduction Package

**Purpose:** Minimum package enabling a third party to reproduce blind test results.

---

## Contents

```
REPRODUCTION_PACKAGE/
├── README.md                           — how to reproduce
├── requirements_frozen.txt             — pip freeze from production .venv
├── random_seeds.json                   — all seed values
├── deterministic_verification.json     — diff(inference_run1, inference_run2)
│
├── model/
│   ├── prior_ALR.pt — prior_SRO.pt    — 21 frozen checkpoint files
│   └── SHA256_CHECKPOINTS.json         — per-file hashes
│
├── config/
│   ├── deploy.py                       — frozen deploy script
│   ├── main.py                         — frozen dashboard
│   └── SHA256_CONFIG.json
│
├── data/
│   ├── merge2026.csv                   — ground truth catalog
│   ├── cosmic_features_v3.csv          — Dst/Kp/hourly
│   └── golden_dataset/                 — 20 tensors (3 stations)
│
├── protocol/
│   ├── SBTP_v2_PROTOCOL.md
│   └── BLIND_TEST_EVIDENCE_SPECIFICATION.md
│
├── pipeline/
│   ├── reproduce.sh                    — shell script: conda install → run → verify
│   └── reproduce.md                    — step-by-step instructions
│
├── verification/
│   ├── EXPECTED_OUTPUT_SHA256.json     — ground-truth output hashes
│   └── verify_reproduction.py          — script: compare expected vs actual
│
└── evidence/
    ├── SHA256_MANIFEST.json            — all package file hashes
    └── SIGNATURE.asc                   — GPG signature of manifest (optional)
```

---

## Reproduction Steps

```bash
# 1. Environment
conda create -n pimes_repro python=3.12
conda activate pimes_repro
pip install -r requirements_frozen.txt

# 2. Seed verification
python -c "import json; print(json.load(open('random_seeds.json')))"

# 3. Checkpoint integrity
sha256sum --check model/SHA256_CHECKPOINTS.json

# 4. Run inference (requires .lem files — provided by BMKG separately)
# The reproduction package does NOT include BMKG waveform data (proprietary).
# The package includes golden_dataset/ for reproduction on preprocessed data.

# 5. Verify outputs
python verification/verify_reproduction.py
# Expected output: "VERIFIED: all outputs match expected SHA256 hashes"
```

---

## Data Restrictions

BMKG waveform data (`.lem` files) is not included due to data ownership. The reproduction package includes:
- Preprocessed golden dataset (20 tensors, 3 stations)
- Ground truth catalog (merge2026.csv)
- Full model checkpoints
- Environment and configuration

Reproduction of the full blind test requires BMKG data access.

---

## Verification Method

```python
# verify_reproduction.py
import json, hashlib

expected = json.load(open("verification/EXPECTED_OUTPUT_SHA256.json"))
actual = {}
for path in expected:
    actual[path] = hashlib.sha256(open(path, "rb").read()).hexdigest()

assert expected == actual, f"Mismatch: {[k for k in expected if expected[k]!=actual[k]]}"
print("VERIFIED: all outputs match expected SHA256 hashes")
```

---

## Constraints

- OS: Ubuntu 22.04 LTS (recommended)
- Python: 3.12.x
- GPU: optional (cpu-only inference also supported)
- RAM: ≥ 16 GB
- Disk: ≥ 50 GB
