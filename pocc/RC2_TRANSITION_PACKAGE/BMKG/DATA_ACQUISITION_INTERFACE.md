# WP3 — Data Acquisition Interface

**Generated:** 2026-07-16

## Purpose

Document the interface for receiving BMKG ULF waveform data when it becomes available.

## Data Reception Workflow

```
1. BMKG transfers data to server
         ↓
2. Place files at: /opt/pimes/data/raw/<STATION>/
         ↓
3. File naming convention:
   YYYYMMDDHHMMSS.lem  (LEMI-30i2 format)
   or station-specific format (e.g., S260611.sta)
         ↓
4. Collector discovery worker picks up new files
         ↓
5. Validation worker verifies integrity
         ↓
6. Runtime trigger processes through pipeline
         ↓
7. CEPSL records integrity evidence
         ↓
8. Dashboard reflects updated status
```

## Directory Structure Required

```
/opt/pimes/data/raw/
├── ALR/          ← ALR station waveform
│   ├── YYYYMMDDHHMMSS.lem
│   └── ...
├── AMB/
├── CLP/
├── DNP/
├── GTO/
├── KPY/
├── LPS/
├── LUT/
├── LWA/
├── LWK/
├── MLB/
├── PLU/
├── SBG/
├── SCN/
├── SKB/
├── SMI/
├── SRG/
├── SRO/
├── TNT/
├── TRT/
└── YOG/
```

## File Requirements

| Requirement | Detail |
|-------------|--------|
| Format | `.lem` (LEMI-30i2 XML + binary) or `.mlb` |
| Sampling | 64 Hz (base 256 Hz / 4 averaging) |
| Channels | 3 (H, D, Z) |
| Bits/sample | 16-bit signed integer |
| Timezone | UTC (file header must specify) |
| Naming | `YYYYMMDDHHMMSS.<ext>` |
| Checksum | SHA256 for each file |
| Coverage | Dec 2025 — Jun 2026 (matching catalog) |

## After Data Is Placed

1. Run: `python deploy.py status` — check collector + pages
2. Run: `python deploy.py doctor` — full health check
3. Check dashboard: `/waveform` — verify coverage updated
4. Verify: collector log shows new discovery entries
