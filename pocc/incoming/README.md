# BMKG Incoming Data Gateway — SOP

**Location:** `d:\opt\pimes\incoming\` (local) → `/opt/pimes/data/raw/` (server)

## Incoming Data Flow

```
BMKG Transfer
     ↓
  incoming/        ← raw data (quarantine)
     ↓
  [validation]     ← checksum, antivirus, metadata, station check
     ↓
  production/      ← validated data (ready for pipeline)
     ↓
  deploy + collector ← automatic processing
```

## Validation Checklist

- [ ] SHA256 checksum matches manifest
- [ ] File extension accepted (.lem, .mlb, .txt, .csv)
- [ ] Timestamp in UTC
- [ ] Station code matches known BMKG stations
- [ ] File size > minimum (10 KB, not empty)
- [ ] Not a duplicate (no existing filename in `prediction_registry.csv`)

## Gateway Directory Structure

```
incoming/
├── <timestamp>_<station>_<filename>  ← quarantine

production/
├── <station>/
│   ├── <filename>                    ← validated, ready

rejected/
├── <reason>_<filename>              ← failed validation
```

## Automated Steps (when data arrives)

```bash
# 1. Verify checksum
cd incoming && sha256sum --check sha256.txt

# 2. Move to production
mv incoming/*.lem production/<STATION>/

# 3. Upload to server via deploy.py
python deploy.py
```
