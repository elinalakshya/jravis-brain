# connectors/template_connector.py
import os, time, logging, json
from datetime import datetime

LOG = logging.getLogger("connector")
LOG.setLevel(logging.INFO)

PLATFORM = os.getenv("PLATFORM_NAME", "template")
RUN_INTERVAL = int(os.getenv("RUN_INTERVAL_S", "300"))


def fetch_tasks():
    """
    Put platform-specific scraping / API fetch here.
    Return list of items (dict) to process, or [].
    """
    # Example: read from a queue, API, or parse dashboard
    return []


def run_once():
    items = fetch_tasks()
    for item in items:
        try:
            # process item, create invoice, update DB, etc.
            LOG.info("%s processed item id=%s", PLATFORM, item.get("id"))
        except Exception as e:
            LOG.exception("Error processing item %s", item)


if __name__ == "__main__":
    LOG.info("Starting connector for %s", PLATFORM)
    while True:
        run_once()
        time.sleep(RUN_INTERVAL)
