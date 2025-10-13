"""
VA_BOT Core v1 – Mission 2040 Executor
---------------------------------------
This module implements VA_BOT: the executor that polls the mission bridge,
performs tasks (placeholder implementations), and reports results back to the bridge.

Features:
 - Connects to mission_bridge.Bridge
 - Polls FIFO task bus for pending tasks
 - Implements a simple dispatcher to run different task handlers
 - Writes progress entries and logs
 - Graceful shutdown on Ctrl+C

How to use:
    python vabot_core_v1.py            # start worker with default poll interval (2s)
    python vabot_core_v1.py --poll 1.0 # start worker with 1s poll interval
    python vabot_core_v1.py --once    # fetch one task, execute, then exit

Notes:
 - Replace placeholder _handle_* methods with real API integration code (Printify, Fiverr, YouTube, etc.)
 - This file expects mission_bridge.py (Bridge class) to be available in same folder
"""

import argparse
import time
import json
import uuid
from datetime import datetime
from mission_bridge import Bridge


class VABot:

    def __init__(self,
                 bridge: Bridge,
                 poll_interval: float = 2.0,
                 worker_name: str = 'VA_BOT'):
        self.bridge = bridge
        self.poll_interval = poll_interval
        self.worker_name = worker_name
        self.running = False

    def start(self, run_once: bool = False):
        """Start the VA_BOT worker loop. If run_once=True, it will process a single task and exit."""
        print(
            f"{self.worker_name} starting (poll {self.poll_interval}s). run_once={run_once}"
        )
        self.running = True
        try:
            while self.running:
                task = self.bridge.fetch_pending_task()
                if not task:
                    if run_once:
                        print(
                            f"{self.worker_name}: no pending tasks found. Exiting (once mode)."
                        )
                        break
                    time.sleep(self.poll_interval)
                    continue
                try:
                    self._process_task(task)
                except Exception as e:
                    # Ensure a failing task is marked as completed with error info to avoid infinite retries
                    err = {
                        'status': 'error',
                        'error': str(e),
                        'timestamp': datetime.utcnow().isoformat()
                    }
                    self.bridge.mark_task_completed(task['id'], err)
                    self.bridge.write_log(
                        'ERROR', f"Worker error processing {task['id']}: {e}")
                if run_once:
                    break
        except KeyboardInterrupt:
            print(f"{self.worker_name} interrupted by user. Shutting down...")
        finally:
            self.running = False
            print(f"{self.worker_name} stopped.")

    def stop(self):
        self.running = False

    def _process_task(self, task: dict):
        tid = task['id']
        self.bridge.write_log(
            'INFO',
            f"{self.worker_name} picked task {tid} ({task['stream_name']}:{task['task_type']})"
        )
        self.bridge.mark_task_started(tid)
        handler = self._get_handler(task['task_type'])
        result = handler(task)
        # Ensure result contains at least a status and timestamp
        result.setdefault('status', 'ok')
        result.setdefault('timestamp', datetime.utcnow().isoformat())
        self.bridge.mark_task_completed(tid, result)
        # Log a progress metric to be picked up by JRAVIS
        metric_key = f"last_{task['task_type']}"
        self.bridge.log_progress(task['stream_id'], metric_key,
                                 json.dumps(result))
        self.bridge.write_log('INFO',
                              f"{self.worker_name} completed task {tid}")

    def _get_handler(self, task_type: str):
        """Return the handler function for a given task_type."""
        mapping = {
            'upload_product': self._handle_upload,
            'add_listing': self._handle_upload,
            'upload_assets': self._handle_upload,
            'upload_reels': self._handle_upload,
            'post_video': self._handle_upload,
            'upload_tracks': self._handle_upload,
            'sync_orders': self._handle_sync,
            'fetch_jobs': self._handle_sync,
            'process_audio': self._handle_sync,
            'deliver_download': self._handle_sync,
            'generate_cv': self._handle_generate_cv,
            'generic_task': self._handle_generic
        }
        return mapping.get(task_type, self._handle_generic)

    # ----------------------
    # Placeholder handlers
    # Replace these with real API calls & logic
    # ----------------------
    def _handle_upload(self, task: dict) -> dict:
        """Simulate uploading a product/asset/video and returning public metadata."""
        time.sleep(1)  # simulate network/upload latency
        item_id = uuid.uuid4().hex[:10]
        public_url = f"https://cdn.mission2040/{item_id}"
        return {
            'status': 'ok',
            'item_id': item_id,
            'public_url': public_url,
            'task_type': task['task_type']
        }

    def _handle_sync(self, task: dict) -> dict:
        """Simulate syncing orders / processing jobs."""
        time.sleep(0.6)
        processed = 1
        return {
            'status': 'ok',
            'processed': processed,
            'task_type': task['task_type']
        }

    def _handle_generate_cv(self, task: dict) -> dict:
        """Simulate generating a CV PDF and returning its filename."""
        time.sleep(0.5)
        fname = f"cv_{uuid.uuid4().hex[:8]}.pdf"
        return {'status': 'ok', 'file': fname, 'task_type': task['task_type']}

    def _handle_generic(self, task: dict) -> dict:
        time.sleep(0.2)
        return {
            'status': 'ok',
            'note': 'generic executed',
            'task_type': task['task_type']
        }


# -------------------------
# CLI
# -------------------------
if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='VA_BOT Core v1 - Executor')
    parser.add_argument('--poll',
                        type=float,
                        default=2.0,
                        help='Poll interval seconds')
    parser.add_argument('--once',
                        action='store_true',
                        help='Fetch one task and exit')
    args = parser.parse_args()

    bridge = Bridge()
    bot = VABot(bridge, poll_interval=args.poll)
    bot.start(run_once=args.once)
