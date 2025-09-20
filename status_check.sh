#!/usr/bin/env bash
# status_check.sh - run connector check, process check, and show latest activation log

set -e

echo "========================================"
echo "🔎 VA Bot Team / Connectors Activation Check"
echo "Date: $(date -u)"
echo "========================================"

echo
echo "-> Step 1: Connector dry-run (no jobs executed)"
python3 check_connectors.py || true

echo
echo "-> Step 2: Are there any running VA Bot processes?"
PIDS=$(pgrep -f phase1_runner.py || true)
if [ -z "$PIDS" ]; then
  echo "ℹ️  No running phase1_runner.py process found."
else
  echo "⚡ phase1_runner.py running with PIDs: $PIDS"
  ps -o pid,cmd -p $PIDS
fi

echo
echo "-> Step 3: Latest activation log (if any)"
LOG=$(ls -1t va_activation_*.log 2>/dev/null | head -n1 || true)
if [ -n "$LOG" ]; then
  echo "📄 Latest log: $LOG (last 200 lines)"
  echo "----------------------------------------"
  tail -n 200 "$LOG" || true
  echo "----------------------------------------"
else
  echo "ℹ️  No activation logs found (va_activation_*.log)."
fi

echo
echo "-> Done. If connectors show errors, fix the missing secrets or credentials listed above."
