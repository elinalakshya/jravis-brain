#!/bin/bash
echo "🚀 Starting VA Bot on Render..."

# Load Google Cloud credentials from ENV into /tmp file
echo "$GOOGLE_APPLICATION_CREDENTIALS_JSON" > /tmp/gcloud-key.json
export GOOGLE_APPLICATION_CREDENTIALS=/tmp/gcloud-key.json

# Run VA Bot main process
python3 vabot/main.py
