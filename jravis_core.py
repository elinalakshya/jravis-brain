# jravis_core.py

```python
"""
jravis_core.py

JRAVIS: the brain. Uses mission_bridge.Bridge to enqueue tasks, generate reports,
and make high-level decisions. This module focuses on planning and reporting.

Usage:
    python jravis_core.py --init
    python jravis_core.py --enqueue-phase 1
    python jravis_core.py --report
"""

import argparse
import uuid
import json
from datetime import datetime
from mission_bridge import Bridge

# Import STREAMS definition. If you keep the streams in a JSON file, load it here.
# For convenience you can keep the streams as a local JSON named 'streams_config.json'.
try:
    with open('streams_config.json', 'r', encoding='utf-8') as f:
        STREAMS = json.load(f)['streams']
except Exception:
    # minimal fallback if file missing
    STREAMS = []

LOCK_CODE = 'LAKSHYA-LOCK-2025'

class JRAVIS:
    def __init__(self, bridge: Bridge, lock_code: str = LOCK_CODE):
        self.bridge = bridge
        self.lock_code = lock_code

    def authorize(self, code: str) -> bool:
        return code == self.lock_code

    def enqueue_phase(self, phase: int) -> int:
        phase_streams = [s for s in STREAMS if s.get('phase') == phase]
        count = 0
        for s in phase_streams:
            task_id = str(uuid.uuid4())
            main_task = s.get('va_bot_tasks', [None])[0] or 'generic_task'
            payload = {"phase": phase, "stream": s.get('name')}
            self.bridge.enqueue_task(task_id, s.get('id'), s.get('name'), main_task, payload)
            count += 1
        self.bridge.write_log('INFO', f'Enqueued {count} tasks for phase {phase}')
        return count

    def generate_report(self, date: str = None) -> dict:
        date = date or datetime.utcnow().date().isoformat()
        rows = self.bridge.get_progress(date)
        report = {}
        for r in rows:
            sid = r['stream_id']
            report.setdefault(sid, {})[r['metric_key']] = r['metric_value']
        self.bridge.write_log('INFO', f'Generated report for {date}')
        return {'date': date, 'report': report}

# CLI
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--init', action='store_true', help='Initialize DB (via bridge)')
    parser.add_argument('--enqueue-phase', type=int, help='Enqueue tasks for phase')
    parser.add_argument('--report', action='store_true', help='Generate today progress report')
    parser.add_argument('--code', type=str, default='', help='Lock code for authorization')
    args = parser.parse_args()

    bridge = Bridge()
    j = JRAVIS(bridge)

    if args.init:
        bridge.write_log('INFO', 'DB initialization requested by JRAVIS CLI')
        print('DB initialized (bridge)')

    if args.enqueue_phase:
        if not j.authorize(args.code):
            print('Authorization failed. Provide correct code with --code')
        else:
            cnt = j.enqueue_phase(args.enqueue_phase)
            print(f'Enqueued {cnt} tasks for phase {args.enqueue_phase}')

    if args.report:
        r = j.generate_report()
        print(json.dumps(r, indent=2))
```

---
