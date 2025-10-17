import os, time, requests, json, logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)

VA_BOT_WEBHOOK = os.getenv("VA_BOT_WEBHOOK",
                           "https://va-bot-connector.onrender.com/execute")
KEY_STORE_URL = os.getenv("KEY_STORE_URL",
                          "https://mission-bridge.onrender.com/api/keystore")
KEY_STORE_TOKEN = os.getenv("KEY_STORE_TOKEN", "LakshyaSecure2040")
CHECK_INTERVAL = 30  # seconds

SYSTEMS = {
    "printify": {
        "env": "PRINTIFY_API_KEY"
    },
    "meshy": {
        "env": "MESHY_API_TOKEN"
    },
    "youtube": {
        "env": "YOUTUBE_API_KEY"
    },
    "fiverr": {
        "env": "FIVERR_API_KEY"
    },
    "shopify": {
        "env": "SHOPIFY_API_KEY"
    },
    "stock": {
        "env": "STOCK_API_KEY"
    },
    "cadcrowd": {
        "env": "CADCROWD_TOKEN"
    },
    "kdp": {
        "env": "KDP_TOKEN"
    },
    "instagram": {
        "env": "INSTAGRAM_TOKEN"
    },
    "stationery": {
        "env": "STATIONERY_KEY"
    }
}


def env_has_key(env_name):
    v = os.getenv(env_name)
    return v is not None and v.strip() != ""


def create_va_bot_task(system_name):
    now = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    plan = {
        "plan_id":
        f"auto-key-{system_name}-{now}",
        "mission":
        "Auto-provision income stream key",
        "stream":
        system_name,
        "actions": [{
            "step": 1,
            "type": "create_account",
            "description": f"Create account for {system_name}"
        }, {
            "step": 2,
            "type": "obtain_api_key",
            "description": f"Request API key for {system_name}"
        }, {
            "step": 3,
            "type": "validate_key",
            "description": "Validate key"
        }, {
            "step": 4,
            "type": "store_key",
            "params": {
                "keystore_url": KEY_STORE_URL,
                "keystore_token": KEY_STORE_TOKEN
            }
        }],
        "fallback": {
            "manual_review": True,
            "notify": "nrveeresh327@gmail.com"
        }
    }

    try:
        r = requests.post(VA_BOT_WEBHOOK, json=plan, timeout=20)
        r.raise_for_status()
        logging.info(f"✅ Sent plan to VA Bot for {system_name}")
    except Exception as e:
        logging.error(f"❌ Failed for {system_name}: {e}")


def main():
    logging.info("🚀 Auto-Key Worker Running...")
    while True:
        for name, meta in SYSTEMS.items():
            if not env_has_key(meta["env"]):
                logging.info(
                    f"🔍 Missing key for {name}. Sending task to VA Bot.")
                create_va_bot_task(name)
            else:
                logging.info(f"✅ {name} key found.")
        time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    main()
