#!/usr/bin/env python3
# va_agent.py — simple watchdog/runner that runs connector.py periodically and ensures it keeps running
import subprocess, time, os, sys, signal, logging, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[0]
CONNECTOR = ROOT / "connector.py"
LOG = ROOT / "va_agent.log"
PING_FILE = ROOT / "va_agent.health"

logging.basicConfig(
    filename=str(LOG),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)


def touch_health():
    try:
        PING_FILE.write_text(time.strftime("%Y-%m-%d %H:%M:%S"))
    except Exception:
        pass


def run_once():
    logging.info("Starting connector.py run")
    try:
        p = subprocess.run(["python3", str(CONNECTOR)],
                           cwd=str(ROOT),
                           timeout=60 * 10,
                           capture_output=True,
                           text=True)
        logging.info("connector.py exit=%s stdout_len=%d stderr_len=%d",
                     p.returncode, len(p.stdout or ""), len(p.stderr or ""))
        if p.stdout:
            logging.info("OUT: %s", p.stdout.strip()[:2000])
        if p.stderr:
            logging.error("ERR: %s", p.stderr.strip()[:4000])
        return p.returncode == 0
    except subprocess.TimeoutExpired:
        logging.error("connector.py timed out")
        return False
    except Exception as e:
        logging.exception("Failed to run connector.py: %s", e)
        return False


def main_loop():
    logging.info("VA Agent starting loop")
    while True:
        touch_health()
        ok = run_once()
        touch_health()
        # if connector returned OK, wait normal cycle. If failed, short retry
        wait = 60 * 15 if ok else 60 * 2
        logging.info("Sleeping for %s seconds (ok=%s)", wait, ok)
        time.sleep(wait)


if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        logging.info("VA Agent stopped by KeyboardInterrupt")
        sys.exit(0)
