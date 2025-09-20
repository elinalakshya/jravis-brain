#!/usr/bin/env bash
set -e

mkdir -p logs

echo "🔗 Starting VA Bot: immediate Phase 1 run + background scheduler…"

# 1) Immediate Phase 1 run NOW
python3 -u vabot/runner_now.py | tee logs/run_now.log

# 2) Start scheduler in background (daily 10:00 IST + weekly Sun 00:00 IST)
if pgrep -f "python3 .*scheduler.py" >/dev/null 2>&1; then
  echo "ℹ️ Scheduler already running."
else
  nohup python3 -u scheduler.py > logs/scheduler.out 2> logs/scheduler.err &
  echo $! > logs/scheduler.pid
  echo "✅ Scheduler PID: $(cat logs/scheduler.pid)"
fi

echo "✅ VA Bot Phase 1 is live."
