import sys
sys.path.insert(0, "/opt/pimes/pocc/collector")
from download_worker import DownloadWorker
from scheduler_engine import manifest

print("IMPORT OK")
w = DownloadWorker("download_test", manifest, interval=1)
try:
    r = w.execute()
    print("RESULT:", r)
except Exception as e:
    print("FAIL:", str(e)[:300])
