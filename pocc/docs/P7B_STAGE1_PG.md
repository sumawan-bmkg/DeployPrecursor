# P7B — Stage 1: PostgreSQL Persistence

## Done
- [x] Create `collector/db.py` — PG connection pool + CRUD for 5 tables
- [x] Create schema SQL (`db_schema.sql`)
- [ ] Run on Ubuntu: create role + database + schema
- [ ] Verify connection from backend
- [ ] Update API endpoints to read from PG

---

## Schema

5 tables + 1 run tracking:
- `predictions` — PK prediction_uuid, idx(station, timestamp)
- `decisions` — PK decision_uuid, FK prediction_uuid
- `fused_events` — PK event_id
- `events` — PK event_id, idx(state)
- `warnings` — PK warning_id, FK event_id, idx(level, state)
- `pipeline_runs` — PK run_id, idx(worker, start_time)

## Files
- **NEW** `collector/db.py`
- **NEW** `collector/db_schema.sql`
- **MODIFY** `backend/main.py` — API routes read from PG

## Deploy Tasks
1. `sudo -u postgres psql -c "CREATE ROLE bmkg LOGIN PASSWORD 'precursor@admin2026!';"`
2. `sudo -u postgres psql -c "CREATE DATABASE pocc OWNER bmkg;"`
3. `psql -U bmkg -d pocc -f /opt/pimes/pocc/collector/db_schema.sql`
4. Deploy collector + backend
5. Verify `curl http://localhost:8500/api/events` returns empty array
