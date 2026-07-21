# Collector SOP — BMKG LAWS V2

## 1. Service Management
```bash
# View status
systemctl status pocc-collector
journalctl -u pocc-collector -n 50 --no-pager

# Start/Stop/Restart
systemctl start pocc-collector
systemctl stop pocc-collector
systemctl restart pocc-collector

# Disable/Enable
systemctl disable pocc-collector
systemctl enable pocc-collector
```

## 2. Data Directory Structure
```
/opt/pimes/pocc/collector/
├── __main__.py          # Worker orchestrator
├── discovery_worker.py  # FTP discovery (300s)
├── download_worker.py   # File download (600s)
├── validation_worker.py # Integrity check (60s)
├── inference_worker.py  # Prediction engine (60s)
├── triggers/            # Scheduler trigger files
├── logs/                # Collector logs
└── events/              # Event definitions

/opt/pimes/data/
├── raw/                 # Raw LEM/h files (per station)
    ├── CUJ/
    ├── MND/
    └── ... (23 stations)
```

## 3. Trigger File Management
Triggers located in `/opt/pimes/pocc/collector/triggers/`:
- `__trigger_discovery`: Triggers discovery cycle
- `__trigger_download`: Triggers download cycle
- `__trigger_validation`: Triggers validation cycle
- `__trigger_inference`: Triggers inference cycle

Clean stale triggers:
```bash
rm /opt/pimes/pocc/collector/triggers/__trigger_*
```

## 4. Log Inspection
```bash
# Latest errors
grep -i "error\|traceback\|exception" /opt/pimes/pocc/collector/collector.log | tail -20

# Cycle times
grep "complete" /opt/pimes/pocc/collector/collector.log | tail -10

# Pipeline status
grep "runtime" /opt/pimes/pocc/collector/collector.log
```
