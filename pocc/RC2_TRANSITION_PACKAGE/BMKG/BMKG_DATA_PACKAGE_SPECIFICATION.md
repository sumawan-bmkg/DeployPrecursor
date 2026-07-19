# WP7 — BMKG Data Package Specification

**Generated:** 2026-07-16

## Data Request Form

| Field | Specification |
|-------|---------------|
| **Organization** | BMKG (Badan Meteorologi, Klimatologi, dan Geofisika) |
| **System** | PIMES — Precursor Identification for Megathrust Earthquake System |
| **Data type** | ULF geomagnetic waveform (fluxgate magnetometer) |
| **Stations requested** | See table below |
| **Period** | 2025-12-01 to 2026-06-30 (7 months) |
| **Sampling rate** | 64 Hz minimum (256 Hz base preferred) |
| **Format accepted** | `.lem` (LEMI-30i2), `.mlb`, `.txt`, `.csv`, MiniSEED |
| **Timezone** | UTC mandatory |
| **Channels** | H (N-S), D (E-W), Z (vertical) |
| **Metadata required** | Station code, latitude, longitude, elevation, sensor type, calibration factor |
| **Checksum** | SHA256 per file mandatory |
| **Naming convention** | `YYYYMMDDHHMMSS.<ext>` |

## Stations Required

| Station | Code | Priors | Signatures | Priority |
|---------|------|--------|------------|----------|
| Alor | ALR | ✅ | ✅ | HIGH |
| Ambon | AMB | ✅ | ✅ | HIGH |
| Cliptok | CLP | ✅ | ✅ | HIGH |
| Denpasar | DNP | – | ✅ | HIGH (has 2018-2019 data) |
| Gorontalo | GTO | ✅ | ✅ | HIGH |
| KPY | KPY | ✅ | ✅ | HIGH |
| Liwa | LPS | ✅ | ✅ | HIGH |
| LUT | LUT | ✅ | ✅ | HIGH |
| LWA | LWA | ✅ | ✅ | HIGH |
| LWK | LWK | ✅ | ✅ | HIGH |
| MLB | MLB | ✅ | ✅ | HIGH |
| PLU | PLU | ✅ | ✅ | HIGH |
| SBG | SBG | ✅ | ✅ | HIGH |
| SCN | SCN | ✅ | ✅ | HIGH |
| SKB | SKB | ✅ | ✅ | HIGH |
| SMG | SMG | ✅ | ✅ | MEDIUM |
| SMI | SMI | ✅ | ✅ | HIGH |
| SRG | SRG | ✅ | ✅ | HIGH |
| SRO | SRO | ✅ | ✅ | HIGH |
| TNT | TNT | ✅ | ✅ | HIGH |
| YOG | YOG | ✅ | ✅ | HIGH |

## Transfer Protocol

1. **Preferred:** Direct SCP/SFTP to server 10.20.229.43
2. **Alternative:** Transfer via removable media to `/opt/pimes/repository/staging/`
3. **Checksum manifest**: Include `sha256.txt` with file list
4. **Verification**: Server will run `sha256sum --check sha256.txt`

## Directory Structure Expected After Transfer

```
/opt/pimes/data/raw/
├── ALR/*.lem
├── AMB/*.lem
├── DNP/*.lem
├── ...
└── sha256.txt
```

## Post-Delivery Actions

Once data arrives, operator runs:
```bash
python deploy.py doctor    # verify system health
# Check /waveform dashboard for coverage update
```
