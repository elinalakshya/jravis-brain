import os, time, json, logging, requests
from datetime import datetime, timezone

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s %(levelname)s bridge: %(message)s")
ENDPOINT = os.getenv("VA_BOT_ENDPOINT")
SECRET = os.getenv("VA_BOT_SECRET")


def send_payload(data):
    headers = {"X-VA-Secret": SECRET, "Content-Type": "application/json"}
    r = requests.post(ENDPOINT, json=data, headers=headers, timeout=15)
    r.raise_for_status()
    logging.info("Sent %s orders to VA Bot", len(data))


def main():
    logging.info("JRAVIS Bridge Core started at %s",
                 datetime.now(timezone.utc))
    while True:
        # simulate order pull from Printify connector or DB
        sample = [{
            "id": "demo-order-1",
            "total": 25.0,
            "currency": "USD",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }]
        try:
            send_payload(sample)
        except Exception as e:
            logging.warning("Push failed: %s", e)
        time.sleep(300)


if __name__ == "__main__":
    main()
