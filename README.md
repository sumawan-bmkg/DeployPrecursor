<img width="1536" height="1024" alt="deploy_abstract" src="https://github.com/user-attachments/assets/3fd6d2d9-5094-4394-88d8-17a07ad0add7" />
# DeployPrecursor

Production deployment repository for PIMES (Precursor Monitoring and Inference System).

This repository contains deployment assets, preprocessing pipelines, inference services, collectors, configuration files, database integration, and operational scripts used to run geomagnetic precursor detection on BMKG infrastructure.

---

# Overview

PIMES is an operational geomagnetic monitoring and inference system that:

1. Collects raw geomagnetic station data.
2. Parses daily SCN/observatory files.
3. Performs signal preprocessing and PC3 extraction.
4. Generates scalogram tensors.
5. Runs deep learning inference using V8 models.
6. Stores prediction results into PostgreSQL.
7. Integrates cosmic indices (Kp and Dst).
8. Supports automated scheduled execution through systemd timers.

---

# Current Deployment Status

## Working Components

- Raw geomagnetic file ingestion
- SCN parser
- Signal preprocessing
- PC3 filtering
- Tensor generation
- Model loading
- Multi-station inference
- PostgreSQL integration
- Kp ingestion (NOAA)
- Dst ingestion (Kyoto WDC)
- Systemd scheduler

## Under Evaluation

- V8 model scientific performance
- Magnitude classification consistency
- Azimuth prediction diversity
- Event detection sensitivity

---

# Repository Structure

```text
.
├── apps/
│   ├── run_station.py
│   ├── run_all_stations.py
│   ├── collect_kp.py
│   ├── collect_dst.py
│   ├── cosmic_db.py
│   └── test_*.py
│
├── collector/
│   └── sftp_collector.py
│
├── config/
│   ├── db.yaml
│   ├── collector.yaml
│   ├── config.yaml
│   ├── system.yaml
│   ├── stations.csv
│   └── model_registry.yaml
│
├── scripts/
│   ├── scn_parser.py
│   ├── preprocessing.py
│   ├── tensor_builder.py
│   ├── inference_runner.py
│   └── utility scripts
│
├── preprocessing/
│   └── core/
│
├── repository/
│   └── staging/
│       └── deploy/
│           ├── models/
│           ├── checkpoints/
│           ├── scripts/
│           └── inference/
│
├── releases/
│
└── README.md
```

---

# System Architecture

```text
Raw Station Files
        │
        ▼
 SCN Parser
        │
        ▼
 Signal Processing
 (PC3 Extraction)
        │
        ▼
 Tensor Generator
        │
        ▼
 Deep Learning Model
        │
        ▼
 Prediction
        │
        ▼
 PostgreSQL
```

---

# Data Sources

## Geomagnetic Stations

Supported station examples:

- ALR
- AMB
- CLP
- GTO
- LPS
- LWK
- MLB
- PLU
- SBG
- SCN
- SKB
- SMI
- SRG
- SRO
- TNT
- TRD
- TRT
- YOG

---

## Kp Index

Source:

NOAA Space Weather Prediction Center

```text
https://services.swpc.noaa.gov
```

---

## Dst Index

Source:

Kyoto World Data Center

```text
https://wdc.kugi.kyoto-u.ac.jp
```

---

# Database

PostgreSQL is used for operational storage.

Main tables:

## predictions

Stores inference results.

Important fields:

```sql
station_code
prediction_time
detection_probability
magnitude_class
azimuth_class
kp
dst
model_version
```

---

## cosmic_indices

Stores space weather indices.

```sql
obs_time
kp
dst
source
```

---

# Environment

Recommended environment:

```text
Ubuntu 24.04 LTS
Python 3.11
PostgreSQL 16
Conda
```

---

# Installation

Clone repository:

```bash
git clone https://github.com/sumawan-bmkg/DeployPrecursor.git

cd DeployPrecursor
```

Create environment:

```bash
conda env create -f repository/staging/deploy/environment.yml

conda activate pimes-prod
```

Install dependencies:

```bash
pip install -r repository/staging/deploy/requirements_exact.txt
```

---

# Running Inference

Single station:

```bash
python apps/run_station.py
```

Multi-station:

```bash
python apps/run_all_stations.py
```

---

# Cosmic Index Collection

Collect Kp:

```bash
python apps/collect_kp.py
```

Collect Dst:

```bash
python apps/collect_dst.py
```

Verify:

```sql
SELECT *
FROM cosmic_indices
ORDER BY obs_time DESC;
```

---

# Scheduler

Example systemd timer:

```text
pimes-inference.timer
```

Runs:

```text
pimes-inference.service
```

which executes:

```bash
python /opt/pimes/apps/run_all_stations.py
```

---

# Verification Checklist

## Parser

```bash
python scripts/parse_real_scn.py
```

Expected:

```text
finite_count = 86400
```

---

## Tensor Generation

Expected:

```text
shape = (3,128,1440)
```

---

## Inference

Expected:

```text
probability
magnitude_class
azimuth
```

returned successfully.

---

## Database

Verify:

```sql
SELECT COUNT(*)
FROM predictions;
```

---

# Backup Strategy

Repository stores:

- Source code
- Configuration
- Deployment scripts
- Model definitions

Repository should NOT store:

- Raw station data
- Runtime logs
- Temporary files
- Database dumps

Excluded through `.gitignore`.

---

# Known Issues

## SCN Station

Current deployment contains empty SCN files:

```text
/opt/pimes/data/raw/SCN/*.SCN
```

These are skipped during inference.

---

## V8 Model Evaluation

Current V8 checkpoint deployment is operational but still undergoing scientific validation.

Observed characteristics:

- Stable inference execution
- Low detection probability range
- Limited azimuth variation
- Magnitude output dominated by class 0

Further model evaluation required.

---

# Maintainer

BMKG

Geomagnetic Monitoring and PIMES Development

Repository:

```text
https://github.com/sumawan-bmkg/DeployPrecursor
```

---

# License

Internal BMKG deployment repository.

Operational use subject to BMKG policies.
