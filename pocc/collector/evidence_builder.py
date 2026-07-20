#!/usr/bin/env python3
"""
evidence_builder.py — Operational Evidence Service (Daily Evidence Builder).

Runs once per day (86400s interval). Queries PostgreSQL for all
operational artefacts and writes structured evidence package to
pdac/evidence/{date}/.

No scientific computation — pure data aggregation + export.
"""
import json, os, logging
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

from collector.scheduler_engine import BaseWorker, manifest, PDAC_DIR
from collector.db import get_pool

log = logging.getLogger("evidence")

EVIDENCE_DIR = PDAC_DIR / "evidence"


class EvidenceBuilder(BaseWorker):
    """Daily export of operational artefacts from PostgreSQL."""

    def execute(self) -> dict:
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        out_dir = EVIDENCE_DIR / today
        os.makedirs(str(out_dir), exist_ok=True)

        pool = get_pool()
        if not pool:
            log.warning("PG unavailable — cannot build evidence")
            return {"error": "PG unavailable"}

        stats = {}
        try:
            # 1. Pipeline runs — today
            stats["pipeline_runs"] = self._dump(
                pool, out_dir, "pipeline_runs",
                "SELECT * FROM pipeline_runs WHERE start_time >= %s ORDER BY start_time",
                (today,)
            )

            # 2. Predictions — today
            stats["predictions"] = self._dump(
                pool, out_dir, "predictions",
                "SELECT * FROM predictions WHERE timestamp >= %s ORDER BY timestamp DESC",
                (today,)
            )

            # 3. Decisions — today
            stats["decisions"] = self._dump(
                pool, out_dir, "decisions",
                "SELECT * FROM decisions WHERE created_at >= %s ORDER BY created_at DESC",
                (today,)
            )

            # 4. Fused events — today
            stats["fused_events"] = self._dump(
                pool, out_dir, "fused_events",
                "SELECT * FROM fused_events WHERE created_at >= %s ORDER BY created_at DESC",
                (today,)
            )

            # 5. Events — today
            stats["events"] = self._dump(
                pool, out_dir, "events",
                "SELECT * FROM events WHERE created_at >= %s ORDER BY created_at DESC",
                (today,)
            )

            # 6. Warnings — today
            stats["warnings"] = self._dump(
                pool, out_dir, "warnings",
                "SELECT * FROM warnings WHERE issued_at >= %s ORDER BY issued_at DESC",
                (today,)
            )

            # 7. Metrics — computed from PG aggregates
            metrics = self._compute_metrics(pool, today)
            self._write_json(out_dir, "metrics.json", metrics)
            stats["metrics"] = len(metrics)

            # 8. Drift — stub for future model drift tracking
            drift = self._compute_drift(pool, today)
            self._write_json(out_dir, "drift.json", drift)
            stats["drift"] = len(drift)

            # 9. Audit summary — today
            stats["audit_summary"] = self._dump(
                pool, out_dir, "audit_summary",
                "SELECT * FROM audit_log WHERE created_at >= %s ORDER BY created_at DESC",
                (today,)
            )

            # 10. Summary file
            summary = {
                "date": today,
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "stats": stats,
                "worker_status": manifest.data.get("workers", {}),
            }
            self._write_json(out_dir, "summary.json", summary)

            # 11. Symlink to latest
            latest_symlink = EVIDENCE_DIR / "latest"
            if latest_symlink.exists() or latest_symlink.is_symlink():
                latest_symlink.unlink()
            try:
                os.symlink(str(out_dir), str(latest_symlink))
            except (OSError, NotImplementedError):
                # Windows or no symlink support — write latest_path
                (EVIDENCE_DIR / "latest_path.txt").write_text(str(out_dir))

            log.info("Evidence built: date=%s stats=%s", today, stats)
            return {"status": "OK", "date": today, **stats}

        except Exception as e:
            log.error("Evidence build failed: %s", e)
            return {"error": str(e)[:200]}

    # ── Helpers ─────────────────────────────────────────

    def _dump(self, pool, out_dir: Path, name: str, query: str, params: tuple) -> int:
        """Run query, write results to JSON, return count."""
        import psycopg2.extras
        conn = pool.getconn()
        try:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(query, params)
                rows = [dict(r, _datetime=str(r.get("_datetime", "")) if hasattr(r.get("_datetime"), "isoformat") else r.get("_datetime"))
                        for r in cur.fetchall()]
            # Convert datetimes to strings
            for row in rows:
                for k, v in list(row.items()):
                    if hasattr(v, "isoformat"):
                        row[k] = v.isoformat()
                    elif hasattr(v, "strftime"):
                        row[k] = v.isoformat()

            self._write_json(out_dir, f"{name}.json", rows)
            return len(rows)
        finally:
            pool.putconn(conn)

    def _compute_metrics(self, pool, date: str) -> dict:
        """Aggregate metrics from today's data."""
        import psycopg2.extras
        conn = pool.getconn()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

            # Avg probability today
            cur.execute("SELECT COALESCE(AVG(probability),0) as avg_prob FROM predictions WHERE timestamp >= %s", (date,))
            avg_prob = float(cur.fetchone()["avg_prob"])

            # Max probability
            cur.execute("SELECT COALESCE(MAX(probability),0) as max_prob FROM predictions WHERE timestamp >= %s", (date,))
            max_prob = float(cur.fetchone()["max_prob"])

            # Decisions by level
            cur.execute("SELECT level, count(*) as n FROM decisions WHERE created_at >= %s GROUP BY level", (date,))
            decisions_by_level = {r["level"]: r["n"] for r in cur.fetchall()}

            # Events by state
            cur.execute("SELECT state, count(*) as n FROM events WHERE created_at >= %s GROUP BY state", (date,))
            events_by_state = {r["state"]: r["n"] for r in cur.fetchall()}

            # Warnings by level
            cur.execute("SELECT level, count(*) as n FROM warnings WHERE issued_at >= %s GROUP BY level", (date,))
            warnings_by_level = {r["level"]: r["n"] for r in cur.fetchall()}

            # Pipeline success rate
            cur.execute("""
                SELECT status, count(*) as n FROM pipeline_runs
                WHERE start_time >= %s GROUP BY status
            """, (date,))
            pipeline_by_status = {r["status"]: r["n"] for r in cur.fetchall()}

            # Station activity
            cur.execute("SELECT station, count(*) as n FROM predictions WHERE timestamp >= %s GROUP BY station ORDER BY n DESC", (date,))
            stations = [{"station": r["station"], "predictions": r["n"]} for r in cur.fetchall()]

            cur.close()
            return {
                "date": date,
                "avg_probability": round(avg_prob, 4),
                "max_probability": round(max_prob, 4),
                "decisions_by_level": decisions_by_level,
                "events_by_state": events_by_state,
                "warnings_by_level": warnings_by_level,
                "pipeline_by_status": pipeline_by_status,
                "stations": stations,
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
        finally:
            pool.putconn(conn)

    def _compute_drift(self, pool, date: str) -> dict:
        """Model drift indicators — stub for future expansion."""
        import psycopg2.extras
        conn = pool.getconn()
        try:
            cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            # Compare today's avg probability vs trailing 7-day
            cur.execute("SELECT COALESCE(AVG(probability),0) FROM predictions WHERE timestamp >= %s", (date,))
            today_avg = float(cur.fetchone()["coalesce"])

            week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).strftime("%Y-%m-%d")
            cur.execute("SELECT COALESCE(AVG(probability),0) FROM predictions WHERE timestamp >= %s AND timestamp < %s",
                       (week_ago, date))
            prev_avg = float(cur.fetchone()["coalesce"])

            drift_pct = ((today_avg - prev_avg) / (prev_avg or 1)) * 100
            cur.close()
            return {
                "date": date,
                "today_avg_probability": round(today_avg, 4),
                "trailing_7day_avg": round(prev_avg, 4),
                "drift_pct": round(drift_pct, 2),
                "status": "NOMINAL" if abs(drift_pct) < 20 else "DRIFT_DETECTED",
                "recorded_at": datetime.now(timezone.utc).isoformat(),
            }
        finally:
            pool.putconn(conn)

    @staticmethod
    def _write_json(out_dir: Path, filename: str, data):
        """Write JSON with logging."""
        path = out_dir / filename
        with open(str(path), "w") as f:
            json.dump(data, f, indent=2, default=str)
        return path
