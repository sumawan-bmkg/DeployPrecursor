#!/bin/bash
# Start collector scheduler on Ubuntu
cd /opt/pimes/pocc

export PYTHONPATH=/opt/pimes/pocc
export PYTHONDONTWRITEBYTECODE=1

KILL_OLD="pkill -f 'CollectorScheduler' 2>/dev/null; true"
eval $KILL_OLD
sleep 1

# Test import first
echo "=== IMPORT TEST ==="
/opt/pimes/laws/runtime/.venv/bin/python -c 'from collector.scheduler_engine import SchedulerManifest; print("SchedulerManifest OK"); from collector.__main__ import CollectorScheduler; print("CollectorScheduler OK")' 2>&1

# Start
echo "=== START ==="
nohup /opt/pimes/laws/runtime/.venv/bin/python -u -c \
  'from collector.__main__ import CollectorScheduler; CollectorScheduler().start()' \
  > /opt/pimes/laws/runtime/validation/pdac/scheduler.log 2>&1 &
echo "PID=$!"

sleep 5

echo "=== STATUS ==="
tail -20 /opt/pimes/laws/runtime/validation/pdac/scheduler.log 2>/dev/null

echo "=== PROCESS ==="
ps aux | grep CollectorScheduler | grep -v grep | head -3

echo "=== DONE ==="
