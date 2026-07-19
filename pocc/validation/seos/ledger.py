"""SEOS Ledger — append-only SQLite database.

No UPDATE. No DELETE. Only INSERT. Immutable audit trail.
"""
import sqlite3, json
from .config import LEDGER_DIR
from .utils import now_iso, new_uuid, sha256_str

_DB_PATH = LEDGER_DIR / "seos_ledger.db"

def _conn():
    conn = sqlite3.connect(str(_DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init():
    """Create tables if not exist."""
    conn = _conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS qualifications (
            id TEXT PRIMARY KEY,
            ts TEXT NOT NULL,
            component TEXT NOT NULL,
            score REAL NOT NULL,
            details TEXT,
            manifest_hash TEXT,
            previous_id TEXT
        );
        CREATE TABLE IF NOT EXISTS drifts (
            id TEXT PRIMARY KEY,
            ts TEXT NOT NULL,
            name TEXT NOT NULL,
            status TEXT NOT NULL,
            trend REAL,
            drift_magnitude REAL,
            confidence REAL,
            details TEXT
        );
        CREATE TABLE IF NOT EXISTS predictions (
            id TEXT PRIMARY KEY,
            ts TEXT NOT NULL,
            station TEXT,
            magnitude REAL,
            confidence REAL,
            prediction_hash TEXT,
            tensor_hash TEXT,
            checkpoint_hash TEXT,
            fingerprint_chain TEXT,
            provenance_uuid TEXT
        );
        CREATE TABLE IF NOT EXISTS evidence (
            id TEXT PRIMARY KEY,
            ts TEXT NOT NULL,
            event_type TEXT NOT NULL,
            component TEXT NOT NULL,
            score REAL,
            status TEXT,
            severity TEXT,
            details TEXT,
            manifest_hash TEXT
        );
        CREATE TABLE IF NOT EXISTS recommendations (
            id TEXT PRIMARY KEY,
            ts TEXT NOT NULL,
            component TEXT NOT NULL,
            severity TEXT NOT NULL,
            cause TEXT,
            confidence REAL,
            action TEXT,
            evidence_ref TEXT
        );
        CREATE TABLE IF NOT EXISTS certificates (
            id TEXT PRIMARY KEY,
            ts TEXT NOT NULL,
            certificate_type TEXT NOT NULL,
            overall_score REAL,
            recommendation TEXT,
            manifest_hash TEXT,
            details TEXT
        );
    """)
    conn.commit()
    conn.close()

def insert(table: str, data: dict):
    """Insert a row into the ledger. Never updates."""
    data["id"] = data.get("id") or new_uuid()
    data["ts"] = data.get("ts") or now_iso()
    cols = ", ".join(data.keys())
    placeholders = ", ".join(["?"] * len(data))
    conn = _conn()
    conn.execute(f"INSERT INTO {table} ({cols}) VALUES ({placeholders})", list(data.values()))
    conn.commit()
    conn.close()
    return data["id"]

def query(table: str, where: str = None, params: tuple = (), limit: int = 100) -> list:
    """Read-only query."""
    conn = _conn()
    sql = f"SELECT * FROM {table}"
    if where: sql += f" WHERE {where}"
    sql += f" ORDER BY ts DESC LIMIT {limit}"
    rows = conn.execute(sql, params).fetchall()
    cols = [d[0] for d in conn.execute(f"SELECT * FROM {table} LIMIT 0").description]
    conn.close()
    return [dict(zip(cols, r)) for r in rows]

def count(table: str) -> int:
    conn = _conn()
    n = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    conn.close()
    return n

def stats() -> dict:
    """Get ledger statistics."""
    tables = ["qualifications", "drifts", "predictions", "evidence", "recommendations", "certificates"]
    return {t: count(t) for t in tables}
