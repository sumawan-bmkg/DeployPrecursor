"""
db_writer_v2.py

Production PostgreSQL writer
Compatible with actual PIMES schema
"""

import logging
from datetime import datetime
from typing import Optional, Dict, List

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor

logger = logging.getLogger(__name__)


class DatabaseWriter:

    def __init__(self, config: Dict):

        self.config = config

        self.pool = psycopg2.pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=config.get("pool_size", 10),
            host=config["host"],
            port=config.get("port", 5432),
            database=config["database"],
            user=config["user"],
            password=config["password"]
        )

        logger.info(
            f"Connected to PostgreSQL: {config['database']}"
        )

    # ==================================================
    # CONNECTIONS
    # ==================================================

    def get_connection(self):
        return self.pool.getconn()

    def return_connection(self, conn):
        self.pool.putconn(conn)

    def close(self):
        self.pool.closeall()

    # ==================================================
    # STATIONS
    # ==================================================

    def get_station(self, station_code: str):

        conn = self.get_connection()

        try:

            with conn.cursor(
                cursor_factory=RealDictCursor
            ) as cur:

                cur.execute(
                    """
                    SELECT *
                    FROM stations
                    WHERE station_code=%s
                    AND active=TRUE
                    """,
                    (station_code,)
                )

                row = cur.fetchone()

                return dict(row) if row else None

        finally:
            self.return_connection(conn)

    def get_active_stations(self):

        conn = self.get_connection()

        try:

            with conn.cursor(
                cursor_factory=RealDictCursor
            ) as cur:

                cur.execute(
                    """
                    SELECT *
                    FROM stations
                    WHERE active=TRUE
                    ORDER BY station_code
                    """
                )

                return [dict(x) for x in cur.fetchall()]

        finally:
            self.return_connection(conn)

    # ==================================================
    # RAW FILES
    # ==================================================

    def insert_raw_file(
        self,
        station_code: str,
        file_date,
        file_path: str,
        file_size: int
    ):

        conn = self.get_connection()

        try:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO raw_files
                    (
                        station_code,
                        file_date,
                        file_path,
                        file_size
                    )
                    VALUES
                    (
                        %s,%s,%s,%s
                    )
                    RETURNING id
                    """,
                    (
                        station_code,
                        file_date,
                        file_path,
                        file_size
                    )
                )

                new_id = cur.fetchone()[0]

                conn.commit()

                return new_id

        except Exception:

            conn.rollback()
            raise

        finally:
            self.return_connection(conn)

    # ==================================================
    # COSMIC INDICES
    # ==================================================

    def insert_cosmic_index(
        self,
        obs_time: datetime,
        kp: float,
        dst: float,
        source: str = "NOAA"
    ):

        conn = self.get_connection()

        try:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO cosmic_indices
                    (
                        obs_time,
                        kp,
                        dst,
                        source
                    )
                    VALUES
                    (
                        %s,%s,%s,%s
                    )
                    RETURNING id
                    """,
                    (
                        obs_time,
                        kp,
                        dst,
                        source
                    )
                )

                idx = cur.fetchone()[0]

                conn.commit()

                return idx

        except Exception:

            conn.rollback()
            raise

        finally:
            self.return_connection(conn)

    def get_latest_cosmic_index(self):

        conn = self.get_connection()

        try:

            with conn.cursor(
                cursor_factory=RealDictCursor
            ) as cur:

                cur.execute(
                    """
                    SELECT *
                    FROM cosmic_indices
                    ORDER BY obs_time DESC
                    LIMIT 1
                    """
                )

                row = cur.fetchone()

                return dict(row) if row else None

        finally:
            self.return_connection(conn)

    # ==================================================
    # PREDICTIONS
    # ==================================================

    def insert_prediction(
        self,
        station_code: str,
        prediction_time: datetime,
        probability: float,
        magnitude_class: int,
        azimuth_class: int,
        kp: float,
        dst: float,
        model_version: str = "v8"
    ):

        conn = self.get_connection()

        try:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO predictions
                    (
                        station_code,
                        prediction_time,
                        detection_probability,
                        magnitude_class,
                        azimuth_class,
                        kp,
                        dst,
                        model_version
                    )
                    VALUES
                    (
                        %s,%s,%s,%s,%s,%s,%s,%s
                    )
                    RETURNING id
                    """,
                    (
                        station_code,
                        prediction_time,
                        probability,
                        magnitude_class,
                        azimuth_class,
                        kp,
                        dst,
                        model_version
                    )
                )

                pred_id = cur.fetchone()[0]

                conn.commit()

                return pred_id

        except Exception:

            conn.rollback()
            raise

        finally:
            self.return_connection(conn)

    def get_recent_predictions(
        self,
        hours: int = 24,
        limit: int = 100
    ):

        conn = self.get_connection()

        try:

            with conn.cursor(
                cursor_factory=RealDictCursor
            ) as cur:

                cur.execute(
                    """
                    SELECT *
                    FROM predictions
                    WHERE prediction_time >=
                        CURRENT_TIMESTAMP
                        - (%s * INTERVAL '1 hour')
                    ORDER BY prediction_time DESC
                    LIMIT %s
                    """,
                    (
                        hours,
                        limit
                    )
                )

                return [
                    dict(x)
                    for x in cur.fetchall()
                ]

        finally:
            self.return_connection(conn)

    # ==================================================
    # ALERTS
    # ==================================================

    def insert_alert(
        self,
        station_code: str,
        probability: float,
        magnitude_class: int,
        azimuth_class: int,
        alert_level: str
    ):

        conn = self.get_connection()

        try:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    INSERT INTO event_alerts
                    (
                        station_code,
                        alert_time,
                        probability,
                        magnitude_class,
                        azimuth_class,
                        alert_level
                    )
                    VALUES
                    (
                        %s,
                        CURRENT_TIMESTAMP,
                        %s,
                        %s,
                        %s,
                        %s
                    )
                    RETURNING id
                    """,
                    (
                        station_code,
                        probability,
                        magnitude_class,
                        azimuth_class,
                        alert_level
                    )
                )

                alert_id = cur.fetchone()[0]

                conn.commit()

                return alert_id

        except Exception:

            conn.rollback()
            raise

        finally:
            self.return_connection(conn)

    def acknowledge_alert(
        self,
        alert_id: int
    ):

        conn = self.get_connection()

        try:

            with conn.cursor() as cur:

                cur.execute(
                    """
                    UPDATE event_alerts
                    SET acknowledged=TRUE
                    WHERE id=%s
                    """,
                    (alert_id,)
                )

                conn.commit()

        except Exception:

            conn.rollback()
            raise

        finally:
            self.return_connection(conn)