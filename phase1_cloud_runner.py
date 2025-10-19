#!/usr/bin/env python3
"""
Phase-1 Cloud Runner — Monitoring Mode
- Starts and monitors:
    * jravis_core_debian.py   (web)
    * scheduler_phase1_cloud.py (background scheduler)
- Optionally runs report_invoice_cloud.py --daily on startup
- Restarts crashed children with exponential backoff
- Pings SERVICE_URL periodically for health checks
- Graceful shutdown on SIGINT/SIGTERM
"""

import os
import sys
import time
import signal
import subprocess
import threading
import requests
from datetime import datetime

# ---------------------------
# CONFIG (via ENV or defaults)
# ---------------------------
CORE_CMD = os.environ.get("CORE_CMD", "python jravis_core_debian.py")
SCHEDULER_CMD = os.environ.get("SCHEDULER_CMD",
                               "python scheduler_phase1_cloud.py")
REPORT_CMD = os.environ.get("REPORT_CMD",
                            "python report_invoice_cloud.py --daily")
RUN_INITIAL_REPORT = os.environ.get("RUN_INITIAL_REPORT",
                                    "true").lower() in ("1", "true", "yes")
SERVICE_URL = os.environ.get("SERVICE_URL", "http://127.0.0.1:3300/")
HEALTH_INTERVAL = int(os.environ.get("HEALTH_INTERVAL_SEC", "60"))
RESTART_BASE_DELAY = float(os.environ.get("RESTART_BASE_DELAY",
                                          "2.0"))  # seconds
LOG_PATH = os.environ.get("PHASE1_LOG", "logs/phase1.log")

os.makedirs(os.path.dirname(LOG_PATH) or ".", exist_ok=True)


# ---------------------------
# Logging helper
# ---------------------------
def log(msg):
    ts = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


# ---------------------------
# Process wrapper class
# ---------------------------
class ManagedProcess:

    def __init__(self, name, cmd):
        self.name = name
        self.cmd = cmd if isinstance(cmd, list) else cmd.split()
        self.proc = None
        self.last_start = None
        self.restart_count = 0
        self._stop = False

    def start(self):
        if self.proc and self.proc.poll() is None:
            log(f"{self.name} already running (pid={self.proc.pid})")
            return
        self.last_start = time.time()
        try:
            log(f"Starting {self.name}: {' '.join(self.cmd)}")
            # Use stdout/stderr passthrough to main logs
            self.proc = subprocess.Popen(self.cmd,
                                         stdout=subprocess.PIPE,
                                         stderr=subprocess.STDOUT,
                                         bufsize=1,
                                         text=True)
            threading.Thread(target=self._stream_logs, daemon=True).start()
            self.restart_count += 1
        except Exception as e:
            log(f"Failed to start {self.name}: {e}")
            self.proc = None

    def _stream_logs(self):
        if not self.proc or not self.proc.stdout:
            return
        try:
            for line in self.proc.stdout:
                log(f"{self.name} | {line.rstrip()}")
        except Exception:
            pass

    def is_running(self):
        return self.proc is not None and self.proc.poll() is None

    def stop(self):
        self._stop = True
        if self.proc and self.proc.poll() is None:
            try:
                log(f"Stopping {self.name} (pid={self.proc.pid})")
                self.proc.terminate()
                wait_secs = 5
                for _ in range(wait_secs * 10):
                    if self.proc.poll() is not None:
                        break
                    time.sleep(0.1)
                if self.proc.poll() is None:
                    log(f"{self.name} did not exit, killing")
                    self.proc.kill()
            except Exception as e:
                log(f"Error stopping {self.name}: {e}")

    def poll(self):
        if not self.proc:
            return None
        return self.proc.poll()


# ---------------------------
# Health checker
# ---------------------------
def health_check_loop(url, interval, stop_event):
    while not stop_event.is_set():
        try:
            r = requests.head(url, timeout=6)
            if r.status_code < 400:
                log(f"Health OK: {url} ({r.status_code})")
            else:
                log(f"Health WARNING: {url} returned status {r.status_code}")
        except Exception as e:
            log(f"Health ERROR: {url} -> {e}")
        stop_event.wait(interval)


# ---------------------------
# Supervisor main
# ---------------------------
def supervisor():
    core = ManagedProcess("JRAVIS-Core", CORE_CMD)
    scheduler = ManagedProcess("JRAVIS-Scheduler", SCHEDULER_CMD)

    # Initial start
    core.start()
    scheduler.start()

    # Optionally run a one-off report at boot
    if RUN_INITIAL_REPORT:
        try:
            log("Running initial report (one-off)")
            rc = subprocess.run(REPORT_CMD.split(),
                                stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT,
                                text=True,
                                timeout=300)
            for ln in rc.stdout.splitlines():
                log("Report | " + ln)
            log(f"Initial report exit code: {rc.returncode}")
        except Exception as e:
            log("Initial report failed: " + str(e))

    # Health checker thread
    stop_event = threading.Event()
    hc_thread = threading.Thread(target=health_check_loop,
                                 args=(SERVICE_URL, HEALTH_INTERVAL,
                                       stop_event),
                                 daemon=True)
    hc_thread.start()

    # Signal handling
    stopped = False

    def _shutdown(signum, frame):
        nonlocal stopped
        if stopped:
            return
        stopped = True
        log(f"Received signal {signum}; shutting down children...")
        stop_event.set()
        core.stop()
        scheduler.stop()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    # Supervisor loop
    while not stopped:
        # Core monitoring
        if not core.is_running():
            exit_code = core.poll()
            log(f"JRAVIS-Core not running (exit={exit_code}) — scheduling restart"
                )
            # backoff
            delay = min(
                RESTART_BASE_DELAY * (2**max(0, core.restart_count - 1)), 300)
            log(f"Restarting JRAVIS-Core in {delay:.1f}s")
            time.sleep(delay)
            core.start()

        # Scheduler monitoring
        if not scheduler.is_running():
            exit_code = scheduler.poll()
            log(f"JRAVIS-Scheduler not running (exit={exit_code}) — scheduling restart"
                )
            delay = min(
                RESTART_BASE_DELAY * (2**max(0, scheduler.restart_count - 1)),
                300)
            log(f"Restarting JRAVIS-Scheduler in {delay:.1f}s")
            time.sleep(delay)
            scheduler.start()

        time.sleep(2)

    # Final wait to let processes exit
    log("Supervisor exiting. Waiting for child processes...")
    time.sleep(1)


if __name__ == "__main__":
    log("Phase1 Cloud Runner starting (Monitoring Mode)")
    try:
        supervisor()
    except Exception as e:
        log("Fatal supervisor error: " + str(e))
        sys.exit(1)
