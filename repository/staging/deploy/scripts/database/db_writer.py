"""
Database Writer - PostgreSQL Integration for ScalogramV3 V8 Production

Purpose: Write predictions, alerts, and logs to PostgreSQL database
"""

import psycopg2
from psycopg2 import pool, extras
import logging
from datetime import datetime
from typing import Optional, Dict, List
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DatabaseWriter:
    """
    PostgreSQL database writer for production deployment
    """
    
    def __init__(self, config: Dict):
        """
        Initialize database connection pool
        
        Args:
            config: Dictionary with database configuration
                - host: PostgreSQL host
                - port: PostgreSQL port
                - database: Database name
                - user: Database user
                - password: Database password
                - pool_size: Connection pool size
        """
        self.config = config
        self.pool = None
        self._initialize_pool()
    
    def _initialize_pool(self):
        """Initialize PostgreSQL connection pool"""
        try:
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=self.config.get('pool_size', 10),
                host=self.config['host'],
                port=self.config.get('port', 5432),
                database=self.config['database'],
                user=self.config['user'],
                password=self.config['password']
            )
            logger.info(f"Database connection pool initialized: {self.config['database']}")
        except Exception as e:
            logger.error(f"Failed to initialize database pool: {e}")
            raise
    
    def get_connection(self):
        """Get connection from pool"""
        return self.pool.getconn()
    
    def return_connection(self, conn):
        """Return connection to pool"""
        self.pool.putconn(conn)
    
    def close_all(self):
        """Close all connections in pool"""
        if self.pool:
            self.pool.closeall()
            logger.info("Database connection pool closed")
    
    # ============================================================
    # STATIONS
    # ============================================================
    
    def get_station_by_code(self, station_code: str) -> Optional[Dict]:
        """
        Get station information by code
        
        Args:
            station_code: Station code (e.g., 'SCN')
            
        Returns:
            Station dictionary or None
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM stations WHERE station_code = %s AND is_active = TRUE",
                    (station_code,)
                )
                result = cur.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error getting station {station_code}: {e}")
            return None
        finally:
            if conn:
                self.return_connection(conn)
    
    def get_all_active_stations(self) -> List[Dict]:
        """Get all active stations"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute("SELECT * FROM v_active_stations")
                results = cur.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting active stations: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)
    
    # ============================================================
    # RAW FILES
    # ============================================================
    
    def insert_raw_file(self, station_id: int, file_date: str, file_path: str,
                       file_size: Optional[int] = None, file_hash: Optional[str] = None) -> int:
        """
        Insert raw file record
        
        Args:
            station_id: Station ID
            file_date: Date of file (YYYY-MM-DD)
            file_path: Local file path
            file_size: File size in bytes
            file_hash: SHA256 hash
            
        Returns:
            file_id or -1 on error
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO raw_files (station_id, file_date, file_path, file_size, file_hash, download_status, download_timestamp)
                    VALUES (%s, %s, %s, %s, %s, 'downloaded', CURRENT_TIMESTAMP)
                    ON CONFLICT (station_id, file_date) 
                    DO UPDATE SET 
                        file_path = EXCLUDED.file_path,
                        file_size = EXCLUDED.file_size,
                        file_hash = EXCLUDED.file_hash,
                        download_status = 'downloaded',
                        download_timestamp = CURRENT_TIMESTAMP
                    RETURNING file_id
                    """,
                    (station_id, file_date, file_path, file_size, file_hash)
                )
                conn.commit()
                return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Error inserting raw file: {e}")
            if conn:
                conn.rollback()
            return -1
        finally:
            if conn:
                self.return_connection(conn)
    
    def update_raw_file_status(self, file_id: int, status: str, error: Optional[str] = None):
        """
        Update raw file download status
        
        Args:
            file_id: File ID
            status: New status (pending, downloaded, failed)
            error: Error message if failed
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE raw_files 
                    SET download_status = %s, download_error = %s, download_timestamp = CURRENT_TIMESTAMP
                    WHERE file_id = %s
                    """,
                    (status, error, file_id)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating raw file status: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                self.return_connection(conn)
    
    # ============================================================
    # PREDICTIONS
    # ============================================================
    
    def insert_prediction(self, station_id: int, prediction_time: datetime,
                         event_probability: float, magnitude: Optional[float] = None,
                         azimuth: Optional[float] = None, kp_index: Optional[float] = None,
                         dst_index: Optional[float] = None, model_version: str = "v8",
                         inference_duration_ms: Optional[int] = None,
                         tensor_path: Optional[str] = None) -> int:
        """
        Insert prediction record
        
        Args:
            station_id: Station ID
            prediction_time: Prediction timestamp
            event_probability: Event probability (0-1)
            magnitude: Predicted magnitude
            azimuth: Predicted azimuth
            kp_index: Kp index used
            dst_index: Dst index used
            model_version: Model version
            inference_duration_ms: Inference duration
            tensor_path: Path to tensor file
            
        Returns:
            prediction_id or -1 on error
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO predictions 
                    (station_id, prediction_time, tensor_path, event_probability, magnitude, azimuth, 
                     kp_index, dst_index, model_version, inference_duration_ms)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING prediction_id
                    """,
                    (station_id, prediction_time, tensor_path, event_probability, magnitude, azimuth,
                     kp_index, dst_index, model_version, inference_duration_ms)
                )
                conn.commit()
                return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Error inserting prediction: {e}")
            if conn:
                conn.rollback()
            return -1
        finally:
            if conn:
                self.return_connection(conn)
    
    def get_recent_predictions(self, station_id: Optional[int] = None, 
                              hours: int = 24, limit: int = 100) -> List[Dict]:
        """
        Get recent predictions
        
        Args:
            station_id: Filter by station (optional)
            hours: Hours back to query
            limit: Maximum results
            
        Returns:
            List of prediction dictionaries
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                if station_id:
                    cur.execute(
                        """
                        SELECT * FROM predictions 
                        WHERE station_id = %s AND prediction_time >= CURRENT_TIMESTAMP - INTERVAL '%s hours'
                        ORDER BY prediction_time DESC
                        LIMIT %s
                        """,
                        (station_id, hours, limit)
                    )
                else:
                    cur.execute(
                        """
                        SELECT * FROM predictions 
                        WHERE prediction_time >= CURRENT_TIMESTAMP - INTERVAL '%s hours'
                        ORDER BY prediction_time DESC
                        LIMIT %s
                        """,
                        (hours, limit)
                    )
                results = cur.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting recent predictions: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)
    
    # ============================================================
    # EVENT ALERTS
    # ============================================================
    
    def insert_alert(self, prediction_id: int, station_id: int, alert_time: datetime,
                    alert_level: str, event_probability: float, magnitude: Optional[float] = None,
                    azimuth: Optional[float] = None, lead_time_hours: Optional[float] = None) -> int:
        """
        Insert event alert
        
        Args:
            prediction_id: Prediction ID
            station_id: Station ID
            alert_time: Alert timestamp
            alert_level: Alert level (low, medium, high, critical)
            event_probability: Event probability
            magnitude: Predicted magnitude
            azimuth: Predicted azimuth
            lead_time_hours: Predicted lead time
            
        Returns:
            alert_id or -1 on error
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO event_alerts 
                    (prediction_id, station_id, alert_time, alert_level, event_probability, 
                     magnitude, azimuth, lead_time_hours)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING alert_id
                    """,
                    (prediction_id, station_id, alert_time, alert_level, event_probability,
                     magnitude, azimuth, lead_time_hours)
                )
                conn.commit()
                return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Error inserting alert: {e}")
            if conn:
                conn.rollback()
            return -1
        finally:
            if conn:
                self.return_connection(conn)
    
    def update_alert_status(self, alert_id: int, status: str, 
                           acknowledged_by: Optional[str] = None):
        """
        Update alert status
        
        Args:
            alert_id: Alert ID
            status: New status (active, acknowledged, resolved)
            acknowledged_by: User who acknowledged
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE event_alerts 
                    SET alert_status = %s, acknowledged_by = %s, acknowledged_at = CURRENT_TIMESTAMP
                    WHERE alert_id = %s
                    """,
                    (status, acknowledged_by, alert_id)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error updating alert status: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                self.return_connection(conn)
    
    def get_active_alerts(self, station_id: Optional[int] = None) -> List[Dict]:
        """Get all active alerts"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                if station_id:
                    cur.execute(
                        "SELECT * FROM v_active_alerts WHERE station_id = %s",
                        (station_id,)
                    )
                else:
                    cur.execute("SELECT * FROM v_active_alerts")
                results = cur.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Error getting active alerts: {e}")
            return []
        finally:
            if conn:
                self.return_connection(conn)
    
    # ============================================================
    # SYSTEM LOGS
    # ============================================================
    
    def insert_log(self, log_level: str, service_name: str, message: str,
                  station_id: Optional[int] = None, error_details: Optional[str] = None,
                  execution_time_ms: Optional[int] = None):
        """
        Insert system log entry
        
        Args:
            log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            service_name: Service name
            message: Log message
            station_id: Station ID (optional)
            error_details: Error details (optional)
            execution_time_ms: Execution time in milliseconds (optional)
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO system_logs 
                    (log_level, service_name, station_id, message, error_details, execution_time_ms)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (log_level, service_name, station_id, message, error_details, execution_time_ms)
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Error inserting log: {e}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                self.return_connection(conn)
    
    # ============================================================
    # COSMIC INDICES
    # ============================================================
    
    def insert_cosmic_index(self, index_time: datetime, kp_index: float, 
                          dst_index: float, source: str = "NOAA") -> int:
        """
        Insert cosmic index record
        
        Args:
            index_time: Index timestamp
            kp_index: Kp index
            dst_index: Dst index
            source: Data source
            
        Returns:
            index_id or -1 on error
        """
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO cosmic_indices (index_time, kp_index, dst_index, source)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (index_time) 
                    DO UPDATE SET 
                        kp_index = EXCLUDED.kp_index,
                        dst_index = EXCLUDED.dst_index
                    RETURNING index_id
                    """,
                    (index_time, kp_index, dst_index, source)
                )
                conn.commit()
                return cur.fetchone()[0]
        except Exception as e:
            logger.error(f"Error inserting cosmic index: {e}")
            if conn:
                conn.rollback()
            return -1
        finally:
            if conn:
                self.return_connection(conn)
    
    def get_latest_cosmic_index(self) -> Optional[Dict]:
        """Get latest cosmic index"""
        conn = None
        try:
            conn = self.get_connection()
            with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
                cur.execute(
                    "SELECT * FROM cosmic_indices ORDER BY index_time DESC LIMIT 1"
                )
                result = cur.fetchone()
                return dict(result) if result else None
        except Exception as e:
            logger.error(f"Error getting latest cosmic index: {e}")
            return None
        finally:
            if conn:
                self.return_connection(conn)


# ============================================================
# FACTORY FUNCTION
# ============================================================

def create_database_writer(config: Dict) -> DatabaseWriter:
    """
    Factory function to create DatabaseWriter instance
    
    Args:
        config: Database configuration dictionary
        
    Returns:
        DatabaseWriter instance
    """
    return DatabaseWriter(config)


if __name__ == "__main__":
    # Test database connection
    test_config = {
        'host': 'localhost',
        'port': 5432,
        'database': 'pimes',
        'user': 'pimes_user',
        'password': 'password',
        'pool_size': 5
    }
    
    try:
        writer = create_database_writer(test_config)
        logger.info("Database writer test successful")
        writer.close_all()
    except Exception as e:
        logger.error(f"Database writer test failed: {e}")
