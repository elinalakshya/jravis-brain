#!/usr/bin/env bash
set -e
mkdir -p logs
# start connectors in background using nohup (or use pm2/supervisor)
nohup python3 connectors/elina_instagram_reels_connector.py  > logs/elina.log 2>&1 &
nohup python3 connectors/printify_pod_connector.py        > logs/printify.log 2>&1 &
nohup python3 connectors/meshy_ai_connector.py           > logs/meshy.log 2>&1 &
nohup python3 connectors/cad_crowd_connector.py          > logs/cadcrowd.log 2>&1 &
nohup python3 connectors/fiverr_ai_connector.py          > logs/fiverr.log 2>&1 &
# add rest...
echo "Connectors started. Check logs/ for output."
