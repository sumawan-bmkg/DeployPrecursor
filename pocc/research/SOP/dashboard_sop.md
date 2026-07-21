# Dashboard SOP — BMKG LAWS V2

## 1. Service Management
```bash
systemctl status pocc-dashboard
systemctl start|stop|restart pocc-dashboard

# Check PID
systemctl show -p MainPID pocc-dashboard.service
```

## 2. Port Configuration
Backend: `uvicorn backend.main:app --host 0.0.0.0 --port 8500`
NGINX reverse proxy: port 8500 → localhost:8500

## 3. Log Management
Dashboard log: `/opt/pimes/pocc/backend/dashboard.log`
View: `tail -f /opt/pimes/pocc/backend/dashboard.log`

## 4. Health Endpoints
- `/api/health` — System health
- `/api/predictor` — Prediction model status
- `/api/overview` — Pipeline overview

## 5. Cache Clearing
```bash
# Restart clears cache
systemctl restart pocc-dashboard
```

## 6. SSL Renewal (if using HTTPS)
```bash
certbot renew --nginx
systemctl reload nginx
```
