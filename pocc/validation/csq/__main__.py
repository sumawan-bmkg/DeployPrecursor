"""CSQ Engine — main entry point.

Usage:
  python -m validation.csq              # run once
  python -m validation.csq --schedule   # run every hour (loop)
  python -m validation.csq --history    # show qualification history
"""
import sys, os, time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

def main():
    args = sys.argv[1:]

    if "--history" in args:
        from validation.csq.config import HISTORY_CSV
        if HISTORY_CSV.exists():
            print(HISTORY_CSV.read_text(encoding="utf-8"))
        else:
            print("No history yet. Run CSQ first.")
        return

    from validation.csq.scheduler import run_once

    if "--schedule" in args:
        print("CSQ Scheduler starting — running every 3600s (1 hour)")
        while True:
            try:
                run_once()
            except Exception as e:
                print(f"CRITICAL: {e}")
            time.sleep(3600)
    else:
        run_once()

if __name__ == "__main__":
    main()
