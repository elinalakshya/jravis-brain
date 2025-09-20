#!/usr/bin/env python3
import os
import sys

# Ensure repo root is on sys.path so "from connector import ..." works
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from datetime import datetime, timedelta
import json
from connectors.phase1_connector import Phase1Connector as MeshyYouTubeConnector


def main():
    # new connector reads all secrets directly from env, no args needed
    c = MeshyYouTubeConnector()

    end = datetime.utcnow()
    start = end - timedelta(days=7)

    data = {"streams": c.get_earnings(start.isoformat(), end.isoformat())}

    fname = f"DailyReport/out/connectors_meshytube_{end.strftime('%Y%m%d')}.json"
    os.makedirs(os.path.dirname(fname), exist_ok=True)
    with open(fname, "w") as f:
        json.dump(data, f, indent=2)
    print("Saved:", fname)


if __name__ == '__main__':
    main()
