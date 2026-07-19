# PIMES Operational Command Center (POCC) — RC1

## Architecture

```
pocc/
├── backend/            # FastAPI + WebSocket + PostgreSQL
│   ├── api/            # REST endpoints
│   ├── core/           # Config, security, DB session
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic
│   └── main.py
├── frontend/           # React + TypeScript + Vite + MUI
│   ├── src/
│   │   ├── components/ # Reusable UI widgets
│   │   ├── pages/      # 10 page views
│   │   ├── hooks/      # Custom hooks
│   │   ├── services/   # API + WebSocket clients
│   │   ├── store/      # State management
│   │   └── App.tsx
│   └── vite.config.ts
├── docker/             # Docker Compose
├── deploy/             # Nginx, systemd
└── docs/               # Documentation
```

## Pages
| # | Page | Route |
|---|------|-------|
| 1 | Mission Control | / |
| 2 | Data Acquisition | /acquisition |
| 3 | Station Map | /stations |
| 4 | Scientific | /scientific |
| 5 | Burn-in | /burnin |
| 6 | Predictions | /predictions |
| 7 | Runtime | /runtime |
| 8 | Infrastructure | /infrastructure |
| 9 | Release | /release |
| 10 | Report Center | /reports |

## Tech Stack
- **Backend**: FastAPI, SQLAlchemy, asyncpg, WebSocket
- **Frontend**: React 18, TypeScript, Vite, MUI 5, Plotly, React-Leaflet, React Flow
- **DB**: PostgreSQL 16
- **Deploy**: Docker Compose, Nginx, systemd
