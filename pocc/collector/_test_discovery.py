#!/usr/bin/env python3
import sys
sys.path.insert(0, "/opt/pimes/pocc/collector")
from discovery_worker import DiscoveryWorker
from scheduler_engine import manifest

print("IMPORT OK")
w = DiscoveryWorker("test", manifest, interval=1)
try:
    r = w.execute()
    print("RESULT:", r.get("total_files", 0), "files")
    print("STATIONS:", r.get("total_stations", 0))
except Exception as e:
    print("FAIL:", str(e)[:200])
