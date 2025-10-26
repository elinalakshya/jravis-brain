#!/usr/bin/env python3
"""
connectors_printify_connectorv3.py
---------------------------------
Production-ready Printify connector (v3) for JRAVIS / Render deployment.

Features:
- Reads PRINTIFY_API_TOKEN and PRINTIFY_SHOP_ID from environment
- Handles rate-limits with backoff and retries
- Lists shops and recent orders
- Ignores removed endpoints gracefully
- Keeps worker alive so Render marks it as healthy
"""

import os
import time
import json
import logging
import requests
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timezone

# -----------------------------------------------------------
# Logging configuration
# -----------------------------------------------------------
logger = logging.getLogger("printify_connector")
logger.setLevel(os.getenv("PRINTIFY_LOG_LEVEL", "INFO").upper())
handler = logging.StreamHandler()
handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
if not logger.handlers:
    logger.addHandler(handler)


# -----------------------------------------------------------
# Exceptions
# -----------------------------------------------------------
class PrintifyError(Exception):
    pass


class PrintifyAuthError(PrintifyError):
    pass


class PrintifyRateLimitError(PrintifyError):
    pass


class PrintifyRequestError(PrintifyError):
    pass


# -----------------------------------------------------------
# Config dataclass
# -----------------------------------------------------------
@dataclass
class PrintifyConfig:
    api_token: str
    api_base: str = "https://api.printify.com/v1"
    default_shop_id: Optional[str] = None
    timeout: int = 30
    max_retries: int = 5
    backoff_factor: float = 1.0

    @classmethod
    def from_env(cls) -> "PrintifyConfig":
        token = os.getenv("PRINTIFY_API_TOKEN")
        if not token:
            raise PrintifyAuthError(
                "PRINTIFY_API_TOKEN not set in environment")
        return cls(
            api_token=token.strip(),
            api_base=os.getenv("PRINTIFY_API_BASE",
                               "https://api.printify.com/v1"),
            default_shop_id=os.getenv("PRINTIFY_SHOP_ID"),
            timeout=int(os.getenv("PRINTIFY_TIMEOUT", "30")),
            max_retries=int(os.getenv("PRINTIFY_MAX_RETRIES", "5")),
            backoff_factor=float(os.getenv("PRINTIFY_BACKOFF_FACTOR", "1.0")),
        )


# -----------------------------------------------------------
# Client
# -----------------------------------------------------------
class PrintifyClient:

    def __init__(self, cfg: PrintifyConfig):
        self.cfg = cfg
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.cfg.api_token}",
            "User-Agent": "jravis-printify-connector/3.0",
            "Accept": "application/json",
        })

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = path if path.startswith("http") else f"{self.cfg.api_base}{path}"
        for attempt in range(1, self.cfg.max_retries + 1):
            try:
                logger.debug("Request %s %s (attempt %d)", method, url,
                             attempt)
                resp = self.session.request(method,
                                            url,
                                            timeout=self.cfg.timeout,
                                            **kwargs)
                if resp.status_code == 401:
                    raise PrintifyAuthError("Unauthorized: bad API token")
                if resp.status_code == 429:
                    raise PrintifyRateLimitError("Rate limit hit")
                if resp.status_code >= 500:
                    raise PrintifyRateLimitError(
                        f"Server error {resp.status_code}")

                if 400 <= resp.status_code < 600:
                    raise PrintifyRequestError(
                        f"HTTP {resp.status_code}: {resp.text}")
                return resp.json()
            except (PrintifyRateLimitError, requests.RequestException) as e:
                wait = self.cfg.backoff_factor * attempt
                logger.warning("Retrying after %.1fs due to: %s", wait, e)
                time.sleep(wait)
        raise PrintifyError(
            f"Request failed after {self.cfg.max_retries} attempts: {url}")

    # -------------------------------
    # API helpers
    # -------------------------------
    def list_shops(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/shops.json")

    def list_orders(self,
                    shop_id: str,
                    limit: int = 10) -> List[Dict[str, Any]]:
        params = {"limit": limit}
        resp = self._request("GET",
                             f"/shops/{shop_id}/orders.json",
                             params=params)
        if isinstance(resp, dict) and "data" in resp:
            return resp["data"]
        return resp if isinstance(resp, list) else []

    def get_print_providers(self):
        # this endpoint removed in v1; will 404
        return self._request("GET", "/print_providers.json")


# -----------------------------------------------------------
# Example run for Render
# -----------------------------------------------------------
def example_run():
    cfg = PrintifyConfig.from_env()
    client = PrintifyClient(cfg)

    logger.info("Starting Printify connector at %s",
                datetime.now(timezone.utc).isoformat())

    # Shops
    try:
        shops = client.list_shops()
        logger.info("Shops: %s", json.dumps(shops, indent=2))
    except Exception as e:
        logger.error("Failed to list shops: %s", e)
        return

    # Pick shop
    shop_id = cfg.default_shop_id or (shops[0].get("id") if shops else None)
    if not shop_id:
        logger.error("No shop ID found.")
        return

    # Orders
    try:
        logger.info("Listing last few orders for shop_id=%s", shop_id)
        orders = client.list_orders(shop_id)
        logger.info("Fetched %d orders", len(orders))
    except Exception as e:
        logger.error("Failed to list orders: %s", e)

    # Providers (handle 404)
    try:
        providers = client.get_print_providers()
        if isinstance(providers, list):
            logger.info("Found %d print providers", len(providers))
        else:
            logger.info("Print providers response: %s", str(providers)[:200])
    except PrintifyRequestError as e:
        if "Not found" in str(e):
            logger.info(
                "Print providers endpoint not available on REST API (expected). Skipping."
            )
        else:
            logger.warning("Could not fetch providers: %s", e)
    except Exception as e:
        logger.warning("Skipping provider fetch: %s", e)

    logger.info("Connector run complete; entering idle loop to stay alive.")
    while True:
        time.sleep(300)


# -----------------------------------------------------------
# Main entry
# -----------------------------------------------------------
if __name__ == "__main__":
    try:
        example_run()
    except PrintifyAuthError as e:
        logger.error("Authentication failed: %s", e)
        time.sleep(60)
    except Exception as e:
        logger.exception("Unhandled error: %s", e)
        time.sleep(60)
