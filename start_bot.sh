# recreate start_bot.sh if needed (safe overwrite)
cat > start_bot.sh <<'PY'
#!/usr/bin/env bash
set -euo pipefail
LOGFILE="va_daemon.log"
DAEMON_CMD="python3 phase1_runner.py --start-daemon --parallel --interval 300"
if [ -z "${MASTER_USER:-}" ] || [ -z "${MASTER_PASS:-}" ]; then
  echo "❌ MASTER_USER or MASTER_PASS not set. Add to Replit Secrets."
  exit 1
fi
if pgrep -f "phase1_runner.py" >/dev/null 2>&1; then
  echo "phase1_runner.py already running. PIDs:"; pgrep -f "phase1_runner.py" || true
else
  echo "Starting daemon..."
  nohup $DAEMON_CMD > "$LOGFILE" 2>&1 &
  sleep 1
  echo "Started. PIDs:"; pgrep -f "phase1_runner.py" || true
fi
if ! pgrep -f "alerts.py" >/dev/null 2>&1; then
  echo "Starting alerts.py..."
  nohup python3 alerts.py >> "${LOGFILE}.alerts" 2>&1 &
fi
if ! pgrep -f "sync_keys_to_secrets.py" >/dev/null 2>&1; then
  echo "Starting sync_keys_to_secrets.py..."
  nohup python3 sync_keys_to_secrets.py >> "${LOGFILE}.sync" 2>&1 &
fi
echo "Tailing log (Ctrl+C to stop):"
tail -f "$LOGFILE"
PY

chmod +x alerts.py sync_keys_to_secrets.py start_bot.sh
# start everything
./start_bot.sh
