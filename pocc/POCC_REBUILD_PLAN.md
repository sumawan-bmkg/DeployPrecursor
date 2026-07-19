# POCC Rebuild Plan

## Architecture Change
```
OLD: FastAPI backend → React SPA (MUI, 333KB JS bundle)
NEW: FastAPI backend → Jinja2 templates + Bootstrap 5 + ECharts
```

## Why
- React SPA too heavy, breaks BMKG operational simplicity
- Server-side rendering = faster loads, easier audit
- Bootstrap 5 = professional control room aesthetic
- ECharts = lighter than Plotly, better for real-time

## Phase 1: Backend (FastAPI + WebSocket + REST)
- main.py: all routes, templates, API, WebSocket
- Data sources: PSEP manifests, RDMC outputs, burn-in logs

## Phase 2: Templates (12 pages)
- base.html (layout, nav, theme toggle)
- dashboard, pipeline, scientific, burnin, stations
- collector, artifacts, analytics, shadow, release, system, audit

## Phase 3: Static Assets
- CSS: BMKG theme, dark/light mode, glassmorphism cards
- JS: ECharts init, WebSocket client, theme toggle
- SVG logo placeholder

## Phase 4: Documentation + Deploy
- README, INSTALL, DEPLOYMENT, USER_GUIDE, OPERATOR_GUIDE
- systemd service + nginx config
- kill old React, deploy new POCC

## Files to create/modify:
- MODIFY: /opt/pimes/pocc/backend/main.py → full rewrite
- NEW: /opt/pimes/pocc/backend/templates/base.html
- NEW: /opt/pimes/pocc/backend/templates/*.html (12 pages)
- NEW: /opt/pimes/pocc/backend/static/css/pocc.css
- NEW: /opt/pimes/pocc/backend/static/js/pocc.js
- NEW: /opt/pimes/pocc/backend/static/img/logo_bmkg.svg
- NEW: /opt/pimes/pocc/backend/data_reader.py
- NEW: /opt/pimes/pocc/docs/*.md
- NEW: /opt/pimes/pocc/deploy.sh
