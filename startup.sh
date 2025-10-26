#!/bin/bash
export PYTHONPATH="/home/runner/workspace/.pythonlibs/lib/python3.9/site-packages:$PYTHONPATH"
export DEPLOY_HOOK_URL="https://api.render.com/deploy/srv-xxxxxx?key=xxxxxxxxxxxx"
echo "🚀 JRAVIS Auto Boot — environment ready"
python phase1_cloud_runner.py
