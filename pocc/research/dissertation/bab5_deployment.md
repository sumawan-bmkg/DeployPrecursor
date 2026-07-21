# Bab V: Deployment dan Operasi

## 5.1 Infrastruktur Server
Server Ubuntu 24.04 LTS:
- CPU: 16 vCPU
- RAM: 16 GB
- Storage: 500 GB SSD
- Network: Gigabit, akses internal BMKG

## 5.2 Systemd Services
Setiap komponen dikelola sebagai systemd service independen:

| Service | PID File | Port | Restart Policy |
|---|---|---|---|
| pocc-dashboard.service | `/run/pocc-dashboard.pid` | 8500 | always, 5s delay |
| pocc-collector.service | `/run/pocc-collector.pid` | — | always, 10s delay |

Service file konfigurasi:
```ini
[Unit]
Description=POCC Dashboard Service
After=network.target postgresql@16-main.service

[Service]
Type=simple
User=bmkg
WorkingDirectory=/opt/pimes/pocc/backend
ExecStart=/home/bmkg/miniconda3/envs/pimes-prod/bin/uvicorn backend.main:app --host 0.0.0.0 --port 8500
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 5.3 PostgreSQL Schema
7 tabel utama:
- `pipeline_runs` (10 kolom, idx worker+start)
- `predictions` (19 kolom, PK prediction_uuid)
- `decisions` (10 kolom, FK prediction_uuid)
- `fused_events` (11 kolom, JSONB input_predictions)
- `events` (9 kolom, idx state+created)
- `warnings` (11 kolom, FK event_id)
- `audit_log` (4 kolom, idx component+created)

## 5.4 NGINX Configuration
Reverse proxy untuk backend:
```nginx
server {
    listen 8500;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8500;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 5.5 Backup Procedures
- Hourly: prediction backup via pg_dump
- Daily: full database backup
- Weekly: konfigurasi sistem
- Retention: 7 hari lokal, 30 hari archive
