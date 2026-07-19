"""OSC entry point.

Usage: python -m validation.osc [--baseline|--daily|--status]
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from validation.osc.runner import run_once, run_daily, run_baseline, show_status

if __name__ == "__main__":
    args = sys.argv[1:]
    if "--baseline" in args: run_baseline()
    elif "--daily" in args: run_daily()
    elif "--status" in args: show_status()
    else: run_once()
