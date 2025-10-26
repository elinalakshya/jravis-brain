#!/usr/bin/env python3
"""
connectors_printify_connectorv3.py

A robust Printify connector (synchronous) with:
- env/config driven setup
- retries/backoff for transient errors
- pagination helpers
- common endpoints: shops, orders, products, uploads
- webhook registration helper
- clear logging and exceptions

Dependencies: requests
"""

from __future__ import annotations
import os
import time
import json
import logging
from typing import Any, Dict, Generator, Optional, List, Tuple
from dataclasses import dataclass
import requests
from requests import Response

# ---------------------------
# Logging
# ---------------------------
logger = logging.getLogger("printify_connector")
logger.setLevel(os.getenv("PRINTIFY_LOG_LEVEL", "INFO"))
_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
if not logger.handlers:
    logger.addHandler(_handler)

# ---------------------------
# Exceptions
# ---------------------------
class PrintifyError(Exception):
    """Base exception for Printify connector"""

class PrintifyAuthError(PrintifyError):
    """Authentication / token error"""

class PrintifyRateLimitError(PrintifyError):
    """Rate limit hit"""

class PrintifyRequestError(PrintifyError):
    """Non-200 response or malformed reply"""

# ---------------------------
# Config dataclass
# ---------------------------
@dataclass
class PrintifyConfig:
    api_token: str
    api_base: str = "https://api.printify.com/v1"
    default_shop_id: Optional[str] = None
    timeout: int = 30
    max_retries: int = 5
    backoff_factor: float = 1.0  # seconds * attempt_number
    user_agent: str = "printify-connector-v3/1.0"

    @classmethod
    def from_env(cls) -> "PrintifyConfig":
        token = os.getenv("PRINTIFY_API_TOKEN", "")
        if not token:
            raise PrintifyAuthError("PRINTIFY_API_TOKEN not set in environment")
        return cls(
            api_token=token.strip(),
            api_base=os.getenv("PRINTIFY_API_BASE", "https://api.printify.com/v1"),
            default_shop_id=os.getenv("PRINTIFY_SHOP_ID"),
            timeout=int(os.getenv("PRINTIFY_TIMEOUT", "30")),
            max_retries=int(os.getenv("PRINTIFY_MAX_RETRIES", "5")),
            backoff_factor=float(os.getenv("PRINTIFY_BACKOFF_FACTOR", "1.0")),
            user_agent=os.getenv("PRINTIFY_USER_AGENT", "printify-connector-v3/1.0"),
        )

# ---------------------------
# Helper functions
# ---------------------------
def safe_json(resp: Response) -> Any:
    try:
        return resp.json()
    except Exception:
        logger.debug("Response text: %s", resp.text)
        raise PrintifyRequestError("Invalid JSON response from Printify API")

def _raise_for_status(resp: Response):
    if resp.status_code == 401:
        raise PrintifyAuthError("Unauthorized: check API token")
    if resp.status_code == 429:
        raise PrintifyRateLimitError("Rate limited by Printify")
    if 400 <= resp.status_code < 600:
        content = safe_json(resp) if resp.text else {"error": resp.text}
        raise PrintifyRequestError(f"HTTP {resp.status_code}: {content}")

# ---------------------------
# Printify Client
# ---------------------------
class PrintifyClient:
    def __init__(self, cfg: PrintifyConfig):
        self.cfg = cfg
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.cfg.api_token}",
            "User-Agent": self.cfg.user_agent,
            "Accept": "application/json",
        })

    # Generic request with retries/backoff
    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Any] = None,
        files: Optional[Dict[str, Any]] = None,
        raw: bool = False,
    ) -> Any:
        url = path if path.startswith("http") else f"{self.cfg.api_base}{path}"
        last_exc: Optional[Exception] = None

        for attempt in range(1, self.cfg.max_retries + 1):
            try:
                logger.debug("Request %s %s (attempt %d)", method, url, attempt)
                resp = self.session.request(
                    method,
                    url,
                    params=params,
                    json=json_body,
                    files=files,
                    timeout=self.cfg.timeout,
                )
                logger.debug("HTTP %d for %s %s", resp.status_code, method, url)

                if resp.status_code in (429, 502, 503, 504):
                    # Rate limit or transient server error -> backoff and retry
                    raise PrintifyRateLimitError(f"Transient HTTP {resp.status_code}")

                _raise_for_status(resp)

                if raw:
                    return resp

                return safe_json(resp)

            except PrintifyRateLimitError as e:
                last_exc = e
                # If printify supplies Retry-After header, honor it
                retry_after = resp.headers.get("Retry-After") if 'resp' in locals() else None
                if retry_after:
                    try:
                        wait = float(retry_after)
                    except Exception:
                        wait = self.cfg.backoff_factor * attempt
                else:
                    wait = self.cfg.backoff_factor * attempt
                logger.warning("Rate limited or server error. Sleeping %.1f seconds (attempt %d)", wait, attempt)
                time.sleep(wait)
                continue
            except PrintifyAuthError:
                # Auth errors should not be retried
                raise
            except requests.RequestException as e:
                last_exc = e
                wait = self.cfg.backoff_factor * attempt
                logger.warning("Network error: %s. Retrying in %.1f seconds (attempt %d)", e, wait, attempt)
                time.sleep(wait)
                continue
            except PrintifyRequestError as e:
                # Non-retryable application-level error (4xx other than 429)
                logger.error("API error: %s", e)
                raise
        # exhausted retries
        raise PrintifyError(f"Request failed after {self.cfg.max_retries} attempts") from last_exc

    # ---------------------------
    # High-level helpers
    # ---------------------------

    # Shops
    def list_shops(self) -> List[Dict[str, Any]]:
        """Return list of shops accessible by the API token."""
        return self._request("GET", "/shops.json")  # returns list

    def get_shop(self, shop_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/shops/{shop_id}.json")

    # Orders
    def list_orders(self, shop_id: Optional[str] = None, status: Optional[str] = None, limit: int = 50) -> Generator[Dict[str, Any], None, None]:
        """Generator paginating through orders. status is optional — e.g., 'new', 'processing', 'fulfilled'."""
        shop_id = shop_id or self.cfg.default_shop_id
        if not shop_id:
            raise ValueError("shop_id required (or set default_shop_id in config)")

        params = {"limit": limit}
        if status:
            params["status"] = status

        page = 1
        while True:
            params["page"] = page
            resp = self._request("GET", f"/shops/{shop_id}/orders.json", params=params)
            # Printify returns list in 'orders' or as list directly; defensive checks
            orders = resp.get("data") if isinstance(resp, dict) and "data" in resp else (resp or [])
            if not orders:
                break
            for o in orders:
                yield o
            page += 1
            # If the returned length < limit, likely last page
            if isinstance(orders, list) and len(orders) < limit:
                break

    def get_order(self, shop_id: str, order_id: int) -> Dict[str, Any]:
        return self._request("GET", f"/shops/{shop_id}/orders/{order_id}.json")

    # Products
    def create_product(self, shop_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a product in a shop.
        payload should follow Printify spec: {title, description, variants, print_areas, ...}
        """
        return self._request("POST", f"/shops/{shop_id}/products.json", json_body=payload)

    def update_product(self, shop_id: str, product_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return self._request("PUT", f"/shops/{shop_id}/products/{product_id}.json", json_body=payload)

    def get_product(self, shop_id: str, product_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/shops/{shop_id}/products/{product_id}.json")

    def delete_product(self, shop_id: str, product_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/shops/{shop_id}/products/{product_id}.json")

    # Upload image (binary)
    def upload_image(self, shop_id: str, image_path: str, filename: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload an image file to printify. Returns uploaded image object.
        NOTE: Printify expects multipart/form-data upload.
        """
        shop_id = shop_id or self.cfg.default_shop_id
        if not shop_id:
            raise ValueError("shop_id required (or set default_shop_id in config)")
        filename = filename or os.path.basename(image_path)
        with open(image_path, "rb") as f:
            files = {"file": (filename, f, "application/octet-stream")}
            return self._request("POST", f"/shops/{shop_id}/uploads/images.json", files=files)

    # Print Providers
    def get_print_providers(self, product_blueprint_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Get list of print providers; optionally filter by blueprint/product type
        """
        params = {}
        if product_blueprint_id:
            params["product_blueprint_id"] = product_blueprint_id
        return self._request("GET", "/print_providers.json", params=params)

    # Webhooks
    def register_webhook(self, callback_url: str, event_types: List[str]) -> Dict[str, Any]:
        """
        Register webhook for current account (across shops). Implementation depends on Printify features.
        payload example: {"callback_url": "...", "event_types": ["orders/create", ...]}
        """
        payload = {"callback_url": callback_url, "event_types": event_types}
        return self._request("POST", "/webhooks.json", json_body=payload)

    def list_webhooks(self) -> List[Dict[str, Any]]:
        return self._request("GET", "/webhooks.json")

    def delete_webhook(self, webhook_id: str) -> Dict[str, Any]:
        return self._request("DELETE", f"/webhooks/{webhook_id}.json")

    # Raw download helper
    def download_file(self, url: str, dest_path: str):
        """Download a file (direct URL) and save to dest_path."""
        resp = self._request("GET", url, raw=True)
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        logger.info("Saved file to %s", dest_path)
        return dest_path

# ---------------------------
# CLI / Example usage
# ---------------------------
def example_run():
    cfg = PrintifyConfig.from_env()
    client = PrintifyClient(cfg)

    # List shops
    try:
        shops = client.list_shops()
        logger.info("Shops: %s", json.dumps(shops, indent=2)[:1000])
    except Exception as e:
        logger.error("Failed to list shops: %s", e)
        return

    shop_id = cfg.default_shop_id or (shops[0].get("id") if shops and isinstance(shops, list) else None)
    if not shop_id:
        logger.error("No shop_id available. Set PRINTIFY_SHOP_ID or ensure token has shops.")
        return

    # Iterate a few orders
    try:
        logger.info("Listing last few orders for shop_id=%s", shop_id)
        for idx, order in enumerate(client.list_orders(shop_id=shop_id, limit=20)):
            logger.info("Order #%d: id=%s status=%s", idx + 1, order.get("id"), order.get("status"))
            if idx >= 4:
                break
    except Exception as e:
        logger.exception("Failed to list orders: %s", e)

    # Get print providers (example)
    try:
        providers = client.get_print_providers()
        logger.info("Found %d print providers", len(providers) if isinstance(providers, list) else 0)
    except Exception as e:
        logger.warning("Could not fetch providers: %s", e)

if __name__ == "__main__":
    # Basic demo run when executed directly.
    # Required env vars: PRINTIFY_API_TOKEN (optionally PRINTIFY_SHOP_ID)
    try:
        example_run()
    except PrintifyAuthError as e:
        logger.error("Auth failure: %s", e)
    except Exception as e:
        logger.exception("Unhandled error: %s", e)
