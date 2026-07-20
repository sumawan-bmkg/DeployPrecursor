#!/usr/bin/env python3
"""
db.py — PostgreSQL persistence for LAWS V2 operational data.

Connection pool, CRUD for all 5 operational tables + pipeline_runs + audit.
Idempotent schema migration on init.
"""
import json, os, logging, uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

try:
    import psycopg2
    import psycopg2.pool
    import psycopg2.extras
    HAS_PSYCOPG2 = True
except ImportError:
    HAS_PSYCOPG2 = False
    psycopg2 = None

log = logging.getLogger("db")

# ── Config ────────────────────────────────────────────────
PG_CONFIG = {
    "host": os.environ.get("PGHOST", "localhost"),
    "port": int(os.environ.get("PGPORT", 5432)),
    "dbname": os.environ.get("PGDATABASE", "pocc"),
    "user": os.environ.get("PGUSER", "bmkg"),
    "password": os.environ.get("PGPASSWORD", "Precursor@2026!"),
    "minconn": 1,
    "maxconn": 5,
}

SCHEMA_PATH = os.path.join(os.path.dirname(__file__), "db_schema.sql")

_pool = None


def get_pool():
    """Lazy-init connection pool."""
    global _pool
    if _pool is None and HAS_PSYCOPG2:
        try:
            _pool = psycopg2.pool.ThreadedConnectionPool(**PG_CONFIG)
            log.info("PG pool ready (host=%s, db=%s)", PG_CONFIG["host"], PG_CONFIG["dbname"])
            _run_migration()
        except Exception as e:
            log.warning("PG unavailable: %s — running in memory-only mode", e)
    return _pool


def _run_migration():
    """Run schema if tables don't exist."""
    if not _pool:
        return
    try:
        with _pool.getconn() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name='predictions')")
                exists = cur.fetchone()[0]
                if not exists and os.path.exists(SCHEMA_PATH):
                    sql = open(SCHEMA_PATH).read()
                    cur.execute(sql)
                    conn.commit()
                    log.info("Schema migration applied")
    except Exception as e:
        log.warning("Migration error: %s", e)


@contextmanager
def _cursor():
    """Get cursor from pool."""
    pool = get_pool()
    if not pool:
        yield None
        return
    conn = pool.getconn()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            yield cur
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        pool.putconn(conn)


# ── Prediction CRUD ───────────────────────────────────────

def save_prediction(prediction) -> bool:
    """Save Prediction object to PG. Returns True on success."""
    if not get_pool():
        return False
    try:
        with _cursor() as cur:
            if cur is None:
                return False
            cur.execute("""
                INSERT INTO predictions (
                    prediction_uuid, station, timestamp, probability, confidence,
                    uncertainty, magnitude, azimuth, explanation, model_version,
                    model_name, backend, latency_ms, artifact_uuid, pipeline_version,
                    qc_version, qc_score, input_hash, prediction_hash
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (prediction_uuid) DO NOTHING
            """, (
                prediction.prediction_uuid,
                prediction.station,
                prediction.timestamp or datetime.now(timezone.utc).isoformat(),
                prediction.probability,
                prediction.confidence,
                prediction.uncertainty,
                getattr(prediction, 'magnitude', None),
                getattr(prediction, 'azimuth', None),
                getattr(prediction, 'explanation', ''),
                prediction.model_version,
                prediction.model_name,
                prediction.backend,
                prediction.latency_ms,
                getattr(prediction, 'artifact_uuid', ''),
                getattr(prediction, 'pipeline_version', ''),
                getattr(prediction, 'qc_version', ''),
                getattr(prediction, 'qc_score', 0.0),
                getattr(prediction, 'input_hash', ''),
                getattr(prediction, 'prediction_hash', ''),
            ))
            return True
    except Exception as e:
        log.error("save_prediction error: %s", e)
        return False


def list_predictions(limit: int = 50, station: str = "") -> List[Dict]:
    if not get_pool():
        return []
    try:
        with _cursor() as cur:
            if cur is None:
                return []
            if station:
                cur.execute("SELECT * FROM predictions WHERE station=%s ORDER BY timestamp DESC LIMIT %s", (station, limit))
            else:
                cur.execute("SELECT * FROM predictions ORDER BY timestamp DESC LIMIT %s", (limit,))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.error("list_predictions error: %s", e)
        return []


# ── Decision CRUD ─────────────────────────────────────────

def save_decision(decision) -> bool:
    if not get_pool():
        return False
    try:
        with _cursor() as cur:
            if cur is None:
                return False
            cur.execute("""
                INSERT INTO decisions (
                    decision_uuid, prediction_uuid, level, probability, confidence,
                    uncertainty, qc_score, triggered_rules, explanation, station
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (decision_uuid) DO NOTHING
            """, (
                decision.decision_uuid,
                decision.prediction_uuid if hasattr(decision, 'prediction_uuid') else '',
                decision.level,
                decision.probability,
                decision.confidence,
                decision.uncertainty,
                decision.qc_score,
                json.dumps(decision.triggered_rules) if hasattr(decision, 'triggered_rules') else '[]',
                decision.explanation,
                decision.station if hasattr(decision, 'station') else '',
            ))
            return True
    except Exception as e:
        log.error("save_decision error: %s", e)
        return False


def list_decisions(limit: int = 50, station: str = "") -> List[Dict]:
    if not get_pool():
        return []
    try:
        with _cursor() as cur:
            if cur is None:
                return []
            if station:
                cur.execute("SELECT * FROM decisions WHERE station=%s ORDER BY created_at DESC LIMIT %s", (station, limit))
            else:
                cur.execute("SELECT * FROM decisions ORDER BY created_at DESC LIMIT %s", (limit,))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.error("list_decisions error: %s", e)
        return []


# ── FusedEvent CRUD ───────────────────────────────────────

def save_fused_event(event) -> bool:
    if not get_pool():
        return False
    try:
        with _cursor() as cur:
            if cur is None:
                return False
            cur.execute("""
                INSERT INTO fused_events (
                    event_id, fused_probability, fused_confidence, n_stations,
                    stations, centroid_lat, centroid_lon, max_distance_km,
                    time_window_start, time_window_end, input_predictions
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (event_id) DO NOTHING
            """, (
                event.event_id,
                event.fused_probability,
                event.fused_confidence,
                event.n_stations,
                event.stations,
                event.centroid_lat if hasattr(event, 'centroid_lat') else None,
                event.centroid_lon if hasattr(event, 'centroid_lon') else None,
                event.max_distance_km if hasattr(event, 'max_distance_km') else None,
                event.time_window_start.isoformat() if hasattr(event, 'time_window_start') and event.time_window_start else None,
                event.time_window_end.isoformat() if hasattr(event, 'time_window_end') and event.time_window_end else None,
                json.dumps(event.input_predictions) if hasattr(event, 'input_predictions') else '[]',
            ))
            return True
    except Exception as e:
        log.error("save_fused_event error: %s", e)
        return False


def list_fused_events(limit: int = 50) -> List[Dict]:
    if not get_pool():
        return []
    try:
        with _cursor() as cur:
            if cur is None:
                return []
            cur.execute("SELECT * FROM fused_events ORDER BY created_at DESC LIMIT %s", (limit,))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.error("list_fused_events error: %s", e)
        return []


# ── Event CRUD ────────────────────────────────────────────

def save_event(event) -> bool:
    if not get_pool():
        return False
    try:
        with _cursor() as cur:
            if cur is None:
                return False
            cur.execute("""
                INSERT INTO events (event_id, state, stations, fused_probability,
                    peak_probability, n_stations, created_at, updated_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (event_id) DO UPDATE SET
                    state=EXCLUDED.state, stations=EXCLUDED.stations,
                    fused_probability=EXCLUDED.fused_probability,
                    peak_probability=GREATEST(events.peak_probability, EXCLUDED.peak_probability),
                    n_stations=EXCLUDED.n_stations, updated_at=NOW()
            """, (
                event.event_id,
                event.state.value if hasattr(event.state, 'value') else event.state,
                event.stations,
                event.fused_probability if hasattr(event, 'fused_probability') else 0,
                event.peak_probability if hasattr(event, 'peak_probability') else event.fused_probability if hasattr(event, 'fused_probability') else 0,
                event.n_stations if hasattr(event, 'n_stations') else 0,
                event.created_at if hasattr(event, 'created_at') else datetime.now(timezone.utc),
                event.updated_at if hasattr(event, 'updated_at') else datetime.now(timezone.utc),
            ))
            return True
    except Exception as e:
        log.error("save_event error: %s", e)
        return False


def list_events(limit: int = 50, state: str = "") -> List[Dict]:
    if not get_pool():
        return []
    try:
        with _cursor() as cur:
            if cur is None:
                return []
            if state:
                cur.execute("SELECT * FROM events WHERE state=%s ORDER BY updated_at DESC LIMIT %s", (state.upper(), limit))
            else:
                cur.execute("SELECT * FROM events ORDER BY updated_at DESC LIMIT %s", (limit,))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.error("list_events error: %s", e)
        return []


def get_event(event_id: str) -> Optional[Dict]:
    if not get_pool():
        return None
    try:
        with _cursor() as cur:
            if cur is None:
                return None
            cur.execute("SELECT * FROM events WHERE event_id=%s", (event_id,))
            r = cur.fetchone()
            return dict(r) if r else None
    except Exception as e:
        log.error("get_event error: %s", e)
        return None


# ── Warning CRUD ──────────────────────────────────────────

def save_warning(warning) -> bool:
    if not get_pool():
        return False
    try:
        with _cursor() as cur:
            if cur is None:
                return False
            cur.execute("""
                INSERT INTO warnings (warning_id, event_id, level, probability,
                    state, stations, reason, issued_at, expired_at, verified_at, retracted_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (warning_id) DO UPDATE SET
                    state=EXCLUDED.state, level=EXCLUDED.level,
                    probability=EXCLUDED.probability, stations=EXCLUDED.stations,
                    reason=EXCLUDED.reason, expired_at=EXCLUDED.expired_at,
                    verified_at=EXCLUDED.verified_at, retracted_at=EXCLUDED.retracted_at
            """, (
                warning.warning_id,
                warning.event_id if hasattr(warning, 'event_id') else '',
                warning.level if hasattr(warning, 'level') else 'WARNING',
                warning.probability if hasattr(warning, 'probability') else 0,
                warning.state.value if hasattr(warning.state, 'value') else (warning.state if hasattr(warning, 'state') else 'NEW'),
                warning.stations if hasattr(warning, 'stations') else [],
                warning.reason if hasattr(warning, 'reason') else '',
                warning.issued_at if hasattr(warning, 'issued_at') else datetime.now(timezone.utc),
                warning.expired_at if hasattr(warning, 'expired_at') else None,
                warning.verified_at if hasattr(warning, 'verified_at') else None,
                warning.retracted_at if hasattr(warning, 'retracted_at') else None,
            ))
            return True
    except Exception as e:
        log.error("save_warning error: %s", e)
        return False


def list_warnings(limit: int = 50, state: str = "") -> List[Dict]:
    if not get_pool():
        return []
    try:
        with _cursor() as cur:
            if cur is None:
                return []
            if state:
                cur.execute("SELECT * FROM warnings WHERE state=%s ORDER BY issued_at DESC LIMIT %s", (state.upper(), limit))
            else:
                cur.execute("SELECT * FROM warnings ORDER BY issued_at DESC LIMIT %s", (limit,))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.error("list_warnings error: %s", e)
        return []


def get_warning(warning_id: str) -> Optional[Dict]:
    if not get_pool():
        return None
    try:
        with _cursor() as cur:
            if cur is None:
                return None
            cur.execute("SELECT * FROM warnings WHERE warning_id=%s", (warning_id,))
            r = cur.fetchone()
            return dict(r) if r else None
    except Exception as e:
        log.error("get_warning error: %s", e)
        return None


# ── PipelineRun CRUD ──────────────────────────────────────

def start_pipeline_run(worker: str) -> Optional[str]:
    """Start a pipeline run. Returns run_id."""
    if not get_pool():
        return None
    run_id = f"run-{uuid.uuid4().hex[:12]}"
    try:
        with _cursor() as cur:
            if cur is None:
                return None
            cur.execute("""
                INSERT INTO pipeline_runs (run_id, worker, start_time, status)
                VALUES (%s,%s,%s,'RUNNING')
            """, (run_id, worker, datetime.now(timezone.utc)))
            return run_id
    except Exception as e:
        log.error("start_pipeline_run error: %s", e)
        return None


def finish_pipeline_run(run_id: str, status: str = "SUCCESS",
                        processed: int = 0, failed: int = 0,
                        latency_ms: float = 0, error: str = ""):
    if not get_pool():
        return
    try:
        with _cursor() as cur:
            if cur is None:
                return
            cur.execute("""
                UPDATE pipeline_runs SET
                    end_time=%s, status=%s, processed_files=%s,
                    failed_files=%s, latency_ms=%s, error=%s
                WHERE run_id=%s
            """, (datetime.now(timezone.utc), status, processed,
                  failed, latency_ms, error[:500] if error else '', run_id))
    except Exception as e:
        log.error("finish_pipeline_run error: %s", e)


def list_pipeline_runs(limit: int = 50, worker: str = "") -> List[Dict]:
    if not get_pool():
        return []
    try:
        with _cursor() as cur:
            if cur is None:
                return []
            if worker:
                cur.execute("SELECT * FROM pipeline_runs WHERE worker=%s ORDER BY start_time DESC LIMIT %s", (worker, limit))
            else:
                cur.execute("SELECT * FROM pipeline_runs ORDER BY start_time DESC LIMIT %s", (limit,))
            return [dict(r) for r in cur.fetchall()]
    except Exception as e:
        log.error("list_pipeline_runs error: %s", e)
        return []


# ── Audit Log ─────────────────────────────────────────────

def audit_log(component: str, action: str, detail: dict = None):
    if not get_pool():
        return
    try:
        with _cursor() as cur:
            if cur is None:
                return
            cur.execute("""
                INSERT INTO audit_log (component, action, detail)
                VALUES (%s,%s,%s)
            """, (component, action, json.dumps(detail or {})))
    except Exception as e:
        log.error("audit_log error: %s", e)


# ── Health ────────────────────────────────────────────────

def check_health() -> dict:
    """Check PG connection. Returns status dict."""
    pool = get_pool()
    if not pool:
        return {"status": "UNAVAILABLE", "driver": HAS_PSYCOPG2}
    try:
        with _cursor() as cur:
            if cur is None:
                return {"status": "UNAVAILABLE", "pool": bool(pool)}
            cur.execute("SELECT 1 AS ok")
            return {"status": "OK", "pool": bool(pool), "driver": HAS_PSYCOPG2}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)[:100]}
