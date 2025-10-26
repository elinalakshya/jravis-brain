#!/usr/bin/env python3
"""
connectors_printify_connectorv3_graphql.py

Printify connector (v3 GraphQL-capable) for JRAVIS / Render.

Features:
- Reads PRINTIFY_API_TOKEN and PRINTIFY_SHOP_ID from environment
- Uses v3 GraphQL endpoint (https://api.printify.com/v3/graphql) for providers & blueprints
- Falls back to v1 REST endpoints where appropriate
- Tolerant GraphQL queries: logs raw responses for quick adaptation
- Rate-limit retries and exponential-ish backoff
- Keeps worker alive on Render (idle loop)
- Configurable via environment variables:
    - FORCE_GRAPHQL=true|false (force GraphQL usage)
    - PRINTIFY_API_BASE (optional override)
    - PRINTIFY_V3_ENDPOINT (optional override)
"""

import os
import time
import json
import logging
import requests
from typing import Any, Dict, Optional, List
from dataclasses import dataclass
from datetime import datetime, timezone

# -----------------------
# Logging
# -----------------------
logger = logging.getLogger("printify_connector")
logger.setLevel(os.getenv("PRINTIFY_LOG_LEVEL", "INFO").upper())
_handler = logging.StreamHandler()
_handler.setFormatter(
    logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
if not logger.handlers:
    logger.addHandler(_handler)


# -----------------------
# Exceptions
# -----------------------
class PrintifyError(Exception):
    pass


class PrintifyAuthError(PrintifyError):
    pass


class PrintifyRateLimitError(PrintifyError):
    pass


class PrintifyRequestError(PrintifyError):
    pass


# -----------------------
# Config
# -----------------------
@dataclass
class PrintifyConfig:
    api_token: str
    api_base: str = "https://api.printify.com/v1"
    v3_endpoint: str = "https://api.printify.com/v3/graphql"
    default_shop_id: Optional[str] = None
    timeout: int = 30
    max_retries: int = 5
    backoff_factor: float = 1.0
    force_graphql: bool = False

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
            v3_endpoint=os.getenv("PRINTIFY_V3_ENDPOINT",
                                  "https://api.printify.com/v3/graphql"),
            default_shop_id=os.getenv("PRINTIFY_SHOP_ID"),
            timeout=int(os.getenv("PRINTIFY_TIMEOUT", "30")),
            max_retries=int(os.getenv("PRINTIFY_MAX_RETRIES", "5")),
            backoff_factor=float(os.getenv("PRINTIFY_BACKOFF_FACTOR", "1.0")),
            force_graphql=os.getenv("FORCE_GRAPHQL", "false").lower()
            in ("1", "true", "yes"),
        )


# -----------------------
# HTTP Client (REST)
# -----------------------
class RestClient:

    def __init__(self, cfg: PrintifyConfig):
        self.cfg = cfg
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.cfg.api_token}",
            "User-Agent": "jravis-printify-connector/graph-1.0",
            "Accept": "application/json",
        })

    def _request(self, method: str, path: str, **kwargs) -> Any:
        url = path if path.startswith("http") else f"{self.cfg.api_base}{path}"
        last_exc = None
        for attempt in range(1, self.cfg.max_retries + 1):
            try:
                logger.debug("REST Request %s %s (attempt %d)", method, url,
                             attempt)
                resp = self.session.request(method,
                                            url,
                                            timeout=self.cfg.timeout,
                                            **kwargs)
                if resp.status_code == 401:
                    raise PrintifyAuthError("Unauthorized: bad API token")
                if resp.status_code == 429:
                    raise PrintifyRateLimitError("REST rate limit hit")
                if resp.status_code >= 500:
                    raise PrintifyRateLimitError(
                        f"REST server error {resp.status_code}")
                if 400 <= resp.status_code < 600:
                    # propagate as request error
                    raise PrintifyRequestError(
                        f"HTTP {resp.status_code}: {resp.text}")
                return resp.json()
            except (PrintifyRateLimitError, requests.RequestException) as e:
                last_exc = e
                wait = self.cfg.backoff_factor * attempt
                logger.warning("REST retry in %.1fs due to: %s", wait, e)
                time.sleep(wait)
                continue
            except PrintifyAuthError:
                raise
            except PrintifyRequestError:
                # don't retry application errors (except when we want to treat certain codes specially)
                raise
        raise PrintifyError(
            f"REST request failed after {self.cfg.max_retries} attempts: {url}"
        ) from last_exc


# -----------------------
# GraphQL Client (v3)
# -----------------------
class GraphQLClient:

    def __init__(self, cfg: PrintifyConfig):
        self.cfg = cfg
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.cfg.api_token}",
            "User-Agent": "jravis-printify-connector/graph-1.0",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })

    def _post(self,
              query: str,
              variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = {"query": query}
        if variables is not None:
            payload["variables"] = variables
        url = self.cfg.v3_endpoint
        last_exc = None
        for attempt in range(1, self.cfg.max_retries + 1):
            try:
                logger.debug("GraphQL POST %s (attempt %d) payload keys: %s",
                             url, attempt, list(payload.keys()))
                resp = self.session.post(url,
                                         json=payload,
                                         timeout=self.cfg.timeout)
                if resp.status_code == 401:
                    raise PrintifyAuthError(
                        "Unauthorized: bad API token for GraphQL")
                if resp.status_code == 429:
                    raise PrintifyRateLimitError("GraphQL rate limit hit")
                if resp.status_code >= 500:
                    raise PrintifyRateLimitError(
                        f"GraphQL server error {resp.status_code}")
                # GraphQL returns 200 but may include "errors" in payload.
                data = resp.json()
                logger.debug("GraphQL raw response: %s",
                             json.dumps(data)[:2000])
                # If HTTP 200 and data contains errors, return and let caller decide.
                return data
            except (PrintifyRateLimitError, requests.RequestException) as e:
                last_exc = e
                wait = self.cfg.backoff_factor * attempt
                logger.warning("GraphQL retry in %.1fs due to: %s", wait, e)
                time.sleep(wait)
                continue
            except PrintifyAuthError:
                raise
        raise PrintifyError(
            f"GraphQL request failed after {self.cfg.max_retries} attempts: {url}"
        ) from last_exc


# -----------------------
# Combined Printify client
# -----------------------
class PrintifyClient:

    def __init__(self, cfg: PrintifyConfig):
        self.cfg = cfg
        self.rest = RestClient(cfg)
        self.gql = GraphQLClient(cfg) if cfg.v3_endpoint else None
        self._gql_supported = cfg.force_graphql

    def list_shops(self) -> List[Dict[str, Any]]:
        # REST endpoint stable for shops
        return self.rest._request("GET", "/shops.json")

    def list_orders(self,
                    shop_id: str,
                    limit: int = 10) -> List[Dict[str, Any]]:
        params = {"limit": limit}
        resp = self.rest._request("GET",
                                  f"/shops/{shop_id}/orders.json",
                                  params=params)
        if isinstance(resp, dict) and "data" in resp:
            return resp["data"]
        return resp if isinstance(resp, list) else []

    # Attempt GraphQL providers query first when available
    def get_print_providers(self) -> List[Dict[str, Any]]:
        # If FORCE_GRAPHQL true, try GraphQL only
        if self.cfg.force_graphql:
            return self._get_print_providers_graphql()
        # Otherwise try REST first, if 404 -> GraphQL
        try:
            return self.rest._request("GET", "/print_providers.json")
        except PrintifyRequestError as e:
            # If REST returns a 404 (Not found), fallback to GraphQL
            if "Not found" in str(e) or "404" in str(e):
                logger.info(
                    "REST print_providers not found — attempting GraphQL fallback."
                )
                return self._get_print_providers_graphql()
            raise

    def _get_print_providers_graphql(self) -> List[Dict[str, Any]]:
        if not self.gql:
            raise PrintifyError("GraphQL endpoint not configured")
        # A tolerant GraphQL query — doesn't assume exact schema fields
        query = """
        query PrintProviders($first: Int) {
          printProviders(first: $first) {
            edges {
              node {
                id
                title
                country
                partner
                metadata
              }
            }
          }
        }
        """
        variables = {"first": 200}
        data = self.gql._post(query, variables=variables)
        # Log full response for quick adaptation
        logger.info("GraphQL printProviders response keys: %s",
                    list(data.keys()))
        if "errors" in data:
            logger.warning("GraphQL returned errors: %s", data["errors"])
        # Try to extract safely
        out = []
        try:
            edges = data.get("data", {}).get("printProviders",
                                             {}).get("edges", [])
            for e in edges:
                node = e.get("node")
                if node:
                    out.append(node)
        except Exception as exc:
            logger.warning("Failed to parse GraphQL providers response: %s",
                           exc)
        return out


# -----------------------
# Example run (Render-friendly)
# -----------------------
def example_run():
    cfg = PrintifyConfig.from_env()
    client = PrintifyClient(cfg)

    logger.info("Starting Printify connector (GraphQL-capable) at %s",
                datetime.now(timezone.utc).isoformat())

    # List shops
    try:
        shops = client.list_shops()
        logger.info("Shops: %s", json.dumps(shops, indent=2))
    except Exception as e:
        logger.error("Failed to list shops: %s", e)
        return

    shop_id = cfg.default_shop_id or (shops[0].get("id") if shops else None)
    if not shop_id:
        logger.error(
            "No shop ID found; ensure PRINTIFY_SHOP_ID is set or the token has shop access."
        )
        return

    # List orders
    try:
        logger.info("Listing last few orders for shop_id=%s", shop_id)
        orders = client.list_orders(shop_id)
        logger.info("Fetched %d orders", len(orders))
    except Exception as e:
        logger.error("Failed to list orders: %s", e)

    # Get providers (GraphQL preferred / fallback)
    try:
        providers = client.get_print_providers()
        if isinstance(providers, list):
            logger.info("Found %d print providers (combined)", len(providers))
        else:
            logger.info("Print providers response (non-list): %s",
                        str(providers)[:400])
    except PrintifyRequestError as e:
        if "Not found" in str(e) or "404" in str(e):
            logger.info(
                "Providers endpoint not found on REST API (expected). Skipping."
            )
        else:
            logger.warning("Could not fetch providers: %s", e)
    except PrintifyAuthError as e:
        logger.error("Auth failed while fetching providers: %s", e)
    except Exception as e:
        logger.warning("Skipping provider fetch due to unexpected error: %s",
                       e)

    logger.info("Connector run complete; entering idle loop to stay alive.")
    while True:
        # You can replace this with periodic work if needed
        time.sleep(300)


# -----------------------
# Entrypoint
# -----------------------
if __name__ == "__main__":
    try:
        example_run()
    except PrintifyAuthError as e:
        logger.error("Authentication failed: %s", e)
        time.sleep(60)
    except Exception as e:
        logger.exception("Unhandled error: %s", e)
        time.sleep(60)
