"""
Scheduler Service - Orchestrate hourly data collection and inference

Purpose: Schedule and coordinate all production services
"""

import schedule
import time
import logging
from datetime import datetime
from pathlib import Path
import subprocess
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ProductionScheduler:
    """
    Production scheduler for ScalogramV3 V8
    """
    
    def __init__(self, script_dir: str):
        """
        Initialize scheduler
        
        Args:
            script_dir: Directory containing service scripts
        """
        self.script_dir = Path(script_dir)
        self.running = False
    
    def run_collector(self):
        """Run FTP collector service"""
        logger.info("Starting FTP collector service")
        try:
            collector_script = self.script_dir / "collector" / "ftp_collector.py"
            result = subprocess.run(
                [sys.executable, str(collector_script)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("FTP collector completed successfully")
            else:
                logger.error(f"FTP collector failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Error running collector: {e}")
    
    def run_preprocessing(self):
        """Run preprocessing service"""
        logger.info("Starting preprocessing service")
        try:
            preprocessing_script = self.script_dir / "preprocessing" / "preprocess_service.py"
            result = subprocess.run(
                [sys.executable, str(preprocessing_script)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("Preprocessing completed successfully")
            else:
                logger.error(f"Preprocessing failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Error running preprocessing: {e}")
    
    def run_inference(self):
        """Run inference service"""
        logger.info("Starting inference service")
        try:
            inference_script = self.script_dir / "inference" / "inference_service.py"
            result = subprocess.run(
                [sys.executable, str(inference_script)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("Inference completed successfully")
            else:
                logger.error(f"Inference failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Error running inference: {e}")
    
    def run_alert_check(self):
        """Run alert generation check"""
        logger.info("Starting alert check")
        try:
            alert_script = self.script_dir / "monitoring" / "alert_manager.py"
            result = subprocess.run(
                [sys.executable, str(alert_script)],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                logger.info("Alert check completed successfully")
            else:
                logger.error(f"Alert check failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Error running alert check: {e}")
    
    def run_full_pipeline(self):
        """Run complete pipeline: collector -> preprocessing -> inference -> alerts"""
        logger.info("=" * 60)
        logger.info("Starting full production pipeline")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        # Step 1: Collector
        self.run_collector()
        
        # Step 2: Preprocessing
        self.run_preprocessing()
        
        # Step 3: Inference
        self.run_inference()
        
        # Step 4: Alert check
        self.run_alert_check()
        
        elapsed = time.time() - start_time
        logger.info("=" * 60)
        logger.info(f"Full pipeline completed in {elapsed:.2f} seconds")
        logger.info("=" * 60)
    
    def setup_schedule(self):
        """Setup scheduled tasks"""
        # Run full pipeline every hour
        schedule.every().hour.do(self.run_full_pipeline)
        
        # Run collector every 30 minutes (more frequent data collection)
        schedule.every(30).minutes.do(self.run_collector)
        
        # Run alert check every 15 minutes (more frequent monitoring)
        schedule.every(15).minutes.do(self.run_alert_check)
        
        logger.info("Schedule configured:")
        logger.info("  - Full pipeline: every hour")
        logger.info("  - Collector: every 30 minutes")
        logger.info("  - Alert check: every 15 minutes")
    
    def start(self):
        """Start scheduler"""
        logger.info("Starting production scheduler")
        self.running = True
        self.setup_schedule()
        
        # Run pipeline immediately on startup
        self.run_full_pipeline()
        
        # Main loop
        while self.running:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    def stop(self):
        """Stop scheduler"""
        logger.info("Stopping production scheduler")
        self.running = False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Production Scheduler for ScalogramV3 V8")
    parser.add_argument("--script-dir", type=str, default="./scripts", help="Directory containing service scripts")
    parser.add_argument("--once", action="store_true", help="Run pipeline once and exit")
    
    args = parser.parse_args()
    
    scheduler = ProductionScheduler(args.script_dir)
    
    if args.once:
        # Run pipeline once and exit
        scheduler.run_full_pipeline()
    else:
        # Run continuous scheduler
        try:
            scheduler.start()
        except KeyboardInterrupt:
            logger.info("Received interrupt, shutting down...")
            scheduler.stop()
