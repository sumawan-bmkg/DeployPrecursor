# ScalogramV3 V8 Production Scripts

**Purpose:** Production orchestration scripts for ScalogramV3 V8 deployment on Ubuntu 24.04

---

## DIRECTORY STRUCTURE

```
scripts/
├── collector/              # FTP data collection
│   └── ftp_collector.py
├── preprocessing/          # Signal processing & tensor generation
│   ├── signal_processing.py
│   ├── polarization.py
│   └── tensor_generator.py
├── inference/              # Model inference
│   └── inference_service.py
├── database/               # PostgreSQL integration
│   ├── schema.sql
│   └── db_writer.py
├── scheduler/              # Job scheduling
│   └── scheduler.py
├── monitoring/             # Health monitoring
│   └── healthcheck.py
├── config/                 # Configuration files
│   └── config.yaml
└── requirements_production.txt
```

---

## INSTALLATION

```bash
# Install Python dependencies
pip install -r requirements_production.txt

# Setup PostgreSQL database
sudo -u postgres psql -f database/schema.sql
```

---

## SERVICES

### 1. FTP Collector

**File:** `collector/ftp_collector.py`

**Purpose:** Download raw magnetometer data from BMKG FTP servers

**Usage:**
```bash
python collector/ftp_collector.py
```

**Configuration:** Edit station configuration in script or provide via config file

---

### 2. Preprocessing Service

**File:** `preprocessing/` (multiple files)

**Purpose:** Process raw data into (3,128,1440) tensors

**Components:**
- `signal_processing.py` - PC3 filtering, gap handling
- `polarization.py` - Polarization feature engineering
- `tensor_generator.py` - CWT scalogram generation with pooling

---

### 3. Inference Service

**File:** `inference/inference_service.py`

**Purpose:** Run model inference on preprocessed tensors

**Usage:**
```bash
python inference/inference_service.py --tensor_path /path/to/tensor.npy
```

---

### 4. Database Writer

**File:** `database/db_writer.py`

**Purpose:** Write predictions, alerts, and logs to PostgreSQL

**Usage:**
```python
from database.db_writer import DatabaseWriter

config = {
    'host': 'localhost',
    'port': 5432,
    'database': 'pimes',
    'user': 'pimes_user',
    'password': 'password'
}

writer = DatabaseWriter(config)
writer.insert_prediction(...)
```

---

### 5. Scheduler

**File:** `scheduler/scheduler.py`

**Purpose:** Orchestrate hourly execution of all services

**Usage:**
```bash
# Run continuous scheduler
python scheduler/scheduler.py

# Run pipeline once
python scheduler/scheduler.py --once
```

**Schedule:**
- Full pipeline: Every hour
- Data collection: Every 30 minutes
- Alert check: Every 15 minutes

---

### 6. Healthcheck

**File:** `monitoring/healthcheck.py`

**Purpose:** HTTP endpoint for health monitoring

**Usage:**
```bash
python monitoring/healthcheck.py --host 0.0.0.0 --port 8080
```

**Endpoints:**
- `GET /health` - Basic health check
- `GET /health/detailed` - Detailed system metrics
- `GET /health/services` - Service status

---

## SYSTEMD SERVICE FILES

### Collector Service

```ini
[Unit]
Description=ScalogramV3 V8 FTP Collector
After=network.target

[Service]
Type=simple
User=pimes
WorkingDirectory=/opt/pimes/scripts
ExecStart=/usr/bin/python3 /opt/pimes/scripts/collector/ftp_collector.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Scheduler Service

```ini
[Unit]
Description=ScalogramV3 V8 Scheduler
After=network.target postgresql.service

[Service]
Type=simple
User=pimes
WorkingDirectory=/opt/pimes/scripts
ExecStart=/usr/bin/python3 /opt/pimes/scripts/scheduler/scheduler.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Healthcheck Service

```ini
[Unit]
Description=ScalogramV3 V8 Healthcheck
After=network.target

[Service]
Type=simple
User=pimes
WorkingDirectory=/opt/pimes/scripts
ExecStart=/usr/bin/python3 /opt/pimes/scripts/monitoring/healthcheck.py --host 0.0.0.0 --port 8080
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

---

## DEPLOYMENT CHECKLIST

- [ ] Install Python 3.10+
- [ ] Install PostgreSQL 14+
- [ ] Create database and schema
- [ ] Install Python dependencies
- [ ] Configure station registry
- [ ] Setup FTP credentials
- [ ] Configure database connection
- [ ] Create systemd service files
- [ ] Enable and start services
- [ ] Configure firewall rules
- [ ] Setup log rotation
- [ ] Configure monitoring alerts

---

## TROUBLESHOOTING

### Service won't start

Check logs:
```bash
journalctl -u pimes-collector -f
journalctl -u pimes-scheduler -f
```

### Database connection failed

Verify PostgreSQL is running:
```bash
sudo systemctl status postgresql
```

Test connection:
```bash
psql -h localhost -U pimes_user -d pimes
```

### FTP download failed

Check network connectivity:
```bash
ping ftp.bmkg.go.id
```

Verify FTP credentials in configuration.

---

## SECURITY NOTES

- Store database credentials in environment variables
- Encrypt FTP passwords in production
- Use SSL/TLS for database connections
- Restrict firewall rules to necessary ports only
- Regular security updates for OS and packages

---

**Version:** 1.0
**Last Updated:** 2025-01-18
