#!/usr/bin/env bash
set -euo pipefail

# Try HTTP trigger first (quiet); if it fails, fall back to running the script directly.
if curl -sfS http://127.0.0.1:10000/send-report >/dev/null 2>&1; then
  echo "HTTP trigger successful — calling /send-report (output below):"
  curl -sS http://127.0.0.1:10000/send-report || true
else
  echo "HTTP trigger failed; running send_daily_report.py directly"
  /usr/bin/env python3 send_daily_report.py --send-now
fi
