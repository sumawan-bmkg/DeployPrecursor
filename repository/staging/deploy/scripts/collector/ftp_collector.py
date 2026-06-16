"""
FTP Collector Service - Collect raw data from BMKG FTP servers

Purpose: Download raw magnetometer data files from 24 BMKG stations via FTP
"""

import ftplib
import os
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
import time
import hashlib

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FTPCollector:
    """
    FTP collector for BMKG magnetometer data
    """
    
    def __init__(self, station_config: Dict, output_dir: str, retry_attempts: int = 3):
        """
        Initialize FTP collector
        
        Args:
            station_config: Station configuration dictionary
                - station_code: Station code
                - ftp_host: FTP server hostname
                - ftp_path: FTP path
                - ftp_username: FTP username
                - ftp_password: FTP password
            output_dir: Directory to store downloaded files
            retry_attempts: Number of retry attempts for failed downloads
        """
        self.station_config = station_config
        self.output_dir = Path(output_dir)
        self.retry_attempts = retry_attempts
        self.station_dir = self.output_dir / station_config['station_code']
        self.station_dir.mkdir(parents=True, exist_ok=True)
    
    def download_file(self, date: datetime) -> Optional[str]:
        """
        Download file for a specific date
        
        Args:
            date: Date to download
            
        Returns:
            Local file path or None on failure
        """
        station_code = self.station_config['station_code']
        ftp_host = self.station_config['ftp_host']
        ftp_path = self.station_config['ftp_path']
        
        # Construct filename (BMKG format: SYYMMDD.STATION)
        yy = date.year % 100
        mm = date.month
        dd = date.day
        filename = f"S{yy:02d}{mm:02d}{dd:02d}.{station_code}"
        
        local_path = self.station_dir / filename
        
        # Check if file already exists
        if local_path.exists():
            logger.info(f"File already exists: {local_path}")
            return str(local_path)
        
        # Attempt download with retries
        for attempt in range(self.retry_attempts):
            try:
                logger.info(f"Downloading {filename} from {ftp_host} (attempt {attempt + 1}/{self.retry_attempts})")
                
                with ftplib.FTP(ftp_host) as ftp:
                    ftp.login(
                        self.station_config['ftp_username'],
                        self.station_config['ftp_password']
                    )
                    
                    # Navigate to station directory
                    station_ftp_path = f"{ftp_path}/{station_code}"
                    ftp.cwd(station_ftp_path)
                    
                    # Download file
                    with open(local_path, 'wb') as f:
                        ftp.retrbinary(f'RETR {filename}', f.write)
                    
                    # Verify file size
                    file_size = local_path.stat().st_size
                    if file_size < 1000:  # Too small, likely error
                        local_path.unlink()
                        raise ValueError(f"File too small: {file_size} bytes")
                    
                    logger.info(f"Successfully downloaded {filename} ({file_size} bytes)")
                    return str(local_path)
                    
            except ftplib.error_perm as e:
                logger.error(f"FTP permission error: {e}")
                if local_path.exists():
                    local_path.unlink()
                return None
            except ftplib.error_temp as e:
                logger.warning(f"FTP temporary error (will retry): {e}")
                time.sleep(2 ** attempt)  # Exponential backoff
            except Exception as e:
                logger.error(f"Download error (attempt {attempt + 1}): {e}")
                if local_path.exists():
                    local_path.unlink()
                if attempt == self.retry_attempts - 1:
                    return None
                time.sleep(2 ** attempt)
        
        return None
    
    def download_date_range(self, start_date: datetime, end_date: datetime) -> Dict[str, str]:
        """
        Download files for a date range
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            Dictionary mapping date to local file path
        """
        results = {}
        current_date = start_date
        
        while current_date <= end_date:
            file_path = self.download_file(current_date)
            if file_path:
                results[current_date.strftime('%Y-%m-%d')] = file_path
            current_date += timedelta(days=1)
        
        return results
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()


class MultiStationCollector:
    """
    Collector for multiple stations
    """
    
    def __init__(self, stations_config: List[Dict], output_dir: str):
        """
        Initialize multi-station collector
        
        Args:
            stations_config: List of station configuration dictionaries
            output_dir: Base output directory
        """
        self.stations_config = stations_config
        self.output_dir = Path(output_dir)
        self.collectors = []
        
        for station_config in stations_config:
            collector = FTPCollector(station_config, output_dir)
            self.collectors.append(collector)
    
    def download_all_stations(self, date: datetime) -> Dict[str, Dict[str, str]]:
        """
        Download data for all stations for a specific date
        
        Args:
            date: Date to download
            
        Returns:
            Dictionary mapping station_code to download results
        """
        results = {}
        
        for collector in self.collectors:
            station_code = collector.station_config['station_code']
            file_path = collector.download_file(date)
            results[station_code] = {
                'success': file_path is not None,
                'file_path': file_path,
                'date': date.strftime('%Y-%m-%d')
            }
        
        return results


if __name__ == "__main__":
    # Example usage
    example_config = {
        'station_code': 'SCN',
        'ftp_host': 'ftp.bmkg.go.id',
        'ftp_path': '/mdata',
        'ftp_username': 'anonymous',
        'ftp_password': 'anonymous@example.com'
    }
    
    collector = FTPCollector(example_config, './data/raw')
    
    # Download today's file
    today = datetime.now()
    file_path = collector.download_file(today)
    
    if file_path:
        logger.info(f"Downloaded: {file_path}")
    else:
        logger.error("Download failed")
