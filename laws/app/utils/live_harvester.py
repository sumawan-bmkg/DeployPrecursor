#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
live_harvester.py — Daemon script for BMKG Live LAWS Data Harvesting & Prediction

Simulates a production client that continually harvests 1440-point geomagnetic 
data across active stations, sends it to the LAWS API, logs the prediction, 
and triggers alerts for significant earthquakes.
"""

import os
import time
import json
import csv
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

import requests
import schedule
import numpy as np

# Configuration
API_URL = os.getenv("LAWS_API_URL", "http://127.0.0.1:8000").rstrip('/')
ACTIVE_STATIONS = ["ALR", "PLU", "YOG", "KPG", "JAI"]
LOG_DIR = Path(__file__).resolve().parents[2] / 'logs'
LOG_FILE = LOG_DIR / 'operational_predictions.csv'

# ANSI Color Codes for Alerting
RED_ALERT = "\033[91m\033[1m"
YELLOW_WARN = "\033[93m"
RESET_COLOR = "\033[0m"


def setup_logger():
    """Ensure the log directory and CSV file exist with correct headers."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        with open(LOG_FILE, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "date_str", "kp_index", "dst_index",
                "storm_mode", "storm_reason", "pipeline", 
                "detection_prob", "detection_class", "earthquake_detected",
                "azimuth_deg", "magnitude", "n_stations", "total_rtt_ms"
            ])


def harvest_space_weather() -> Tuple[float, float]:
    """
    Simulate harvesting live space weather parameters from NOAA/SWPC.
    In a real scenario, this would query a JSON feed.
    """
    # Generate realistic variations around calm weather
    kp = max(0.0, min(9.0, random.gauss(2.5, 1.5)))
    dst = max(-500.0, min(50.0, random.gauss(-10.0, 20.0)))
    return round(kp, 1), round(dst, 1)


def harvest_station_data(station: str) -> Dict[str, Any]:
    """
    Simulate harvesting the last 24 minutes (1440 samples @ 1Hz) for a station.
    Injects a synthetic ULF signature occasionally for testing.
    """
    # Base background noise
    raw_h = np.random.randn(1440) * 15.0
    raw_d = np.random.randn(1440) * 12.0
    raw_z = np.random.randn(1440) * 20.0
    
    # 5% chance to inject a synthetic ULF anomaly (magnitude ~5.0 proxy)
    if random.random() < 0.05:
        anomaly = np.sin(np.linspace(0, 10 * np.pi, 1440)) * 500.0
        raw_h += anomaly
        raw_d += anomaly * 0.5
        raw_z += anomaly * 0.8
        
    return {
        "station_id": station,
        "raw_h": raw_h.tolist(),
        "raw_d": raw_d.tolist(),
        "raw_z": raw_z.tolist()
    }


def execute_harvest_and_predict():
    """Main job function executed by the scheduler."""
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 🔄 Initiating Live Harvest cycle...")
    
    # 1. Harvest Space Weather
    kp_val, dst_val = harvest_space_weather()
    date_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    
    # 2. Harvest Station Data
    signals = []
    # Pick a random subset of 3-5 active stations
    n_st = random.randint(3, len(ACTIVE_STATIONS))
    stations_polled = random.sample(ACTIVE_STATIONS, n_st)
    
    for st in stations_polled:
        signals.append(harvest_station_data(st))
        
    payload = {
        "date": date_str,
        "kp_index": kp_val,
        "dst_index": dst_val,
        "raw_signals": signals
    }
    
    # 3. Post to LAWS Operational API
    t_start = time.perf_counter()
    try:
        resp = requests.post(f"{API_URL}/predict", json=payload, timeout=30)
        resp.raise_for_status()
        result = resp.json()
    except Exception as e:
        print(f"  ❌ Failed to communicate with API at {API_URL}: {e}")
        return
        
    t_rtt = (time.perf_counter() - t_start) * 1000
    
    # 4. Extract metrics & log to CSV
    log_prediction(result, t_rtt)
    
    # 5. Alerting Engine (Simulated Webhook / Sirens)
    process_alerts(result)


def log_prediction(result: Dict[str, Any], rtt_ms: float):
    """Log the API response to the operational CSV database."""
    try:
        with open(LOG_FILE, mode='a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                result.get("timestamp", ""),
                result.get("date", ""),
                result.get("kp_raw", 0),
                result.get("dst_raw", 0),
                result.get("storm_mode", False),
                result.get("storm_reason", ""),
                result.get("pipeline", ""),
                round(result.get("detection_prob", 0), 4),
                result.get("detection_class", 0),
                result.get("earthquake_detected", False),
                round(result.get("azimuth_deg", 0), 1),
                round(result.get("magnitude", 0), 2),
                result.get("n_stations", 0),
                round(rtt_ms, 2)
            ])
    except Exception as e:
        print(f"  ❌ Failed to write to log file: {e}")


def process_alerts(result: Dict[str, Any]):
    """Evaluate response and trigger red alerts if conditions are met."""
    eq_detected = result.get("earthquake_detected", False)
    mag = result.get("magnitude", 0.0)
    prob = result.get("detection_prob", 0.0)
    
    if result.get("storm_mode"):
        print(f"  {YELLOW_WARN}⚡ GEOMAGNETIC STORM DETECTED (Gate Closed) - Inference Bypassed.{RESET_COLOR}")
        return

    if eq_detected and mag > 4.5:
        # MAGNITUDE > 4.5 TRIGGER
        print(f"\n{RED_ALERT}🚨🚨🚨 CRITICAL EARTHQUAKE ALERT 🚨🚨🚨{RESET_COLOR}")
        print(f"{RED_ALERT}  Time: {result['timestamp']}{RESET_COLOR}")
        print(f"{RED_ALERT}  Magnitude: Mw {mag:.2f} (Est.){RESET_COLOR}")
        print(f"{RED_ALERT}  Azimuth: {result['azimuth_deg']:.1f}°{RESET_COLOR}")
        print(f"{RED_ALERT}  Confidence: {prob * 100:.1f}%{RESET_COLOR}")
        print(f"{RED_ALERT}  Stations Triggered: {', '.join(result.get('stations_used', []))}{RESET_COLOR}")
        print(f"{RED_ALERT}🚨🚨🚨 DISPATCHING WEBHOOK TO BMKG INA-TEWS 🚨🚨🚨{RESET_COLOR}\n")
    elif eq_detected:
        # MINOR EQ TRIGGER
        print(f"  {YELLOW_WARN}⚠️ Minor Seismic Activity Detected (Mw {mag:.2f}, {prob*100:.1f}% conf). No Action Required.{RESET_COLOR}")
    else:
        print(f"  ✅ Status Normal. No significant anomalies. (V9.5 Prob: {prob:.3f})")


def main():
    print(f"Starting BMKG Live Data Harvester...")
    print(f"API Endpoint: {API_URL}")
    print(f"Log File: {LOG_FILE}")
    
    setup_logger()
    
    # Run once immediately
    execute_harvest_and_predict()
    
    # Schedule to run every 5 minutes
    schedule.every(5).minutes.do(execute_harvest_and_predict)
    
    print("\n⏳ Harvester daemon active. Polling every 5 minutes. Press Ctrl+C to stop.\n")
    
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Harvester shutdown by user.")

if __name__ == "__main__":
    main()
