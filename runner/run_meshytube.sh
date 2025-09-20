#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.." || exit 1
# Ensure env vars (set these in Replit Secrets)
: "${MESHY_API_KEY:?set MESHY_API_KEY}"
: "${YOUTUBE_CLIENT_ID:?set YOUTUBE_CLIENT_ID}"
: "${YOUTUBE_CLIENT_SECRET:?set YOUTUBE_CLIENT_SECRET}"
python3 DailyReport/capture_meshytube.py
