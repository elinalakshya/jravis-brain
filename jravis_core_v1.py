"""
JRAVIS Core v1 – Mission 2040 Brain System
-------------------------------------------
This module forms the core controller for Mission 2040.
It reads streams_config.json, manages task planning, and coordinates with the mission_bridge.

Functions:
 - Authorize with lock code
 - Enqueue daily tasks by phase
 - Generate daily/weekly reports
 - Log progress into mission_bridge

Usage:
    python jravis_core_v1.py --init
    python jravis_core_v1.py --phase 1 --code LAKSHYA-LOCK-2025
    python jravis_core_v1.py --report
"""

import argparse
import uuid
import json
from datetime import datetime
from mission_bridge import Bridge

LOCK_CODE = 'LAKSHYA-LOCK-2025'


class JRAVIS:

    def __init__(self,
                 bridge: Bridge,
                 config_path: str = 'streams_config.json',
                 lock_code: str = LOCK_CODE):
        self.bridge = bridge
        self.config_path = config_path
        self.lock_code = lock_code
        self.streams = self._load_streams()

    def _load_streams(self):
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('streams', []) if isinstance(data,
                                                             dict) else data
        except Exception as e:
            self.bridge.write_log('ERROR',
                                  f'Failed to load streams config: {e}')
            return []

    def authorize(self, code: str) -> bool:
        return code == self.lock_code

    def list_streams(self, phase: int):
        filtered = [s for s in self.streams if s.get('phase') == phase]
        print(f'\n📘 Streams in Phase {phase}: {len(filtered)}')
        for s in filtered:
            print(
                f"  [{s['id']}] {s['name']}  →  Income: ₹{s['monthly_range_inr']['min']}–₹{s['monthly_range_inr']['max']}/mo"
            )
        return filtered

    def enqueue_phase(self, phase: int):
        streams = [s for s in self.streams if s.get('phase') == phase]
        count = 0
        for s in streams:
            main_task = s.get('va_bot_tasks', [None])[0] or 'generic_task'
            task_id = str(uuid.uuid4())
            payload = {
                'phase': phase,
                'stream_name': s.get('name'),
                'income_source': s.get('income_source'),
                'timestamp': datetime.utcnow().isoformat()
            }
            self.bridge.enqueue_task(task_id, s.get('id'), s.get('name'),
                                     main_task, payload)
            count += 1
        self.bridge.write_log(
            'INFO', f'JRAVIS: Enqueued {count} tasks for Phase {phase}')
        print(
            f'\n✅ JRAVIS successfully enqueued {count} tasks for Phase {phase}.'
        )
        return count

    def generate_report(self, date: str = None):
        date = date or datetime.utcnow().date().isoformat()
        records = self.bridge.get_progress(date)
        summary = {}
        for r in records:
            sid = r['stream_id']
            summary.setdefault(sid, {})[r['metric_key']] = r['metric_value']
        print(
            f'\n📊 JRAVIS Daily Report ({date})\n-----------------------------------'
        )
        for sid, metrics in summary.items():
            stream = next((s for s in self.streams if s['id'] == sid), None)
            name = stream['name'] if stream else f'ID {sid}'
            print(f'▶ {name}')
            for k, v in metrics.items():
                print(f'   • {k}: {v}')
        if not summary:
            print('No progress logged yet.')
        self.bridge.write_log('INFO', f'Report generated for {date}')
        return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='JRAVIS Core v1 Controller')
    parser.add_argument('--init',
                        action='store_true',
                        help='Initialize DB (Bridge)')
    parser.add_argument('--phase',
                        type=int,
                        help='Phase number (1|2|3) to enqueue')
    parser.add_argument('--code',
                        type=str,
                        default='',
                        help='Authorization code')
    parser.add_argument('--report',
                        action='store_true',
                        help='Generate daily report')
    args = parser.parse_args()

    bridge = Bridge()
    jravis = JRAVIS(bridge)

    if args.init:
        bridge.write_log('INFO', 'JRAVIS: Initialized mission bridge DB')
        print('Mission Bridge initialized successfully.')

    if args.phase:
        if not jravis.authorize(args.code):
            print(
                '🚫 Authorization failed! Enter correct code (--code LAKSHYA-LOCK-2025)'
            )
        else:
            jravis.list_streams(args.phase)
            jravis.enqueue_phase(args.phase)

    if args.report:
        jravis.generate_report()
