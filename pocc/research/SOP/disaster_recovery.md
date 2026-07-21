# Disaster Recovery SOP — BMKG LAWS V2

## 1. RPO/RTO Definitions
| Tier | RPO | RTO | Target |
|---|---|---|---|
| Predictions DB | < 1 hour | < 15 min | Hot standby via pg_dump |
| Raw Data | < 24 hours | < 1 hour | Daily rsync to secondary |
| Configuration | < 1 week | < 30 min | Weekly config backup |

## 2. Backup Schedule
```bash
# Hourly prediction backup
0 * * * * pg_dump -U bmkg -h localhost pimes -t predictions | gzip > /opt/pimes/backups/predictions_$(date +\%Y\%m\%d_\%H).sql.gz

# Daily full DB backup
0 3 * * * pg_dump -U bmkg -h localhost pimes | gzip > /opt/pimes/backups/full_$(date +\%Y\%m\%d).sql.gz

# Weekly config backup
0 4 * * 0 tar czf /opt/pimes/backups/config_$(date +\%Y\%m\%d).tar.gz /opt/pimes/pocc/ /opt/pimes/laws/
```

## 3. Restore Procedures

### 3.1 Database Restore
```bash
# Drop and recreate
sudo -u postgres psql -c "DROP DATABASE IF EXISTS pimes;"
sudo -u postgres psql -c "CREATE DATABASE pimes;"

# Restore from dump
gunzip -c /opt/pimes/backups/full_<date>.sql.gz | sudo -u postgres psql -d pimes
```

### 3.2 Data Restore
```bash
# rsync from secondary (if configured)
rsync -avz secondary:/opt/pimes/data/raw/ /opt/pimes/data/raw/
```

### 3.3 Service Restore
```bash
# Restart all services after restore
systemctl restart pocc-collector
systemctl restart pocc-dashboard
```

## 4. DR Drill Schedule
Quarterly (Jan, Apr, Jul, Oct):
1. Backup restoration to test DB
2. Service failover test
3. Full recovery timeline measurement
4. Report with improvement recommendations
