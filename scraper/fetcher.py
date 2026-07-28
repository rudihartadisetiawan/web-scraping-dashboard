"""eBay Browse API fetcher for the Global Marketplace Price & Trend Monitor.

Credentials are read from environment variables only.
"""

from __future__ import annotations

import base64
import logging
import os
import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

# ponytail: allow running the script directly from the scraper folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import requests
from sqlalchemy import text
from sqlalchemy.engine import Engine

from scraper.db import get_connection

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

_ENVIRONMENTS = {
    "PRODUCTION": {
        "auth": "https://api.ebay.com/identity/v1/oauth2/token",
        "browse": "https://api.ebay.com/buy/browse/v1/item_summary/search",
    },
    "SANDBOX": {
        "auth": "https://api.sandbox.ebay.com/identity/v1/oauth2/token",
        "browse": "https://api.sandbox.ebay.com/buy/browse/v1/item_summary/search",
    },
}

_SOURCE = "ebay"
_KEYWORD = "sneakers"
_LIMIT = 50
_MAX_PAGES = 5
_PRICE_FILTER = "price:[20..300],priceCurrency:USD"
_SORT = "price"

_TOKEN_CACHE: dict[str, Any] = {"token": None, "expires_at": 0.0}


def _env_urls() -> dict[str, str]:
    env = os.environ.get("EBAY_ENVIRONMENT", "SANDBOX").upper()
    return _ENVIRONMENTS.get(env, _ENVIRONMENTS["SANDBOX"])


def _request_with_retry(method: str, url: str, **kwargs: Any) -> requests.Response:
    """Make an HTTP request with exponential backoff and 429 handling."""
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            response = requests.request(method, url, timeout=30, **kwargs)

            if response.status_code == 429:
                retry_after = response.headers.get("Retry-After")
                wait = (
                    int(retry_after)
                    if retry_after and str(retry_after).isdigit()
                    else 2 ** attempt
                )
                logger.warning("Rate limited (429) on %s; retry after %ss", url, wait)
                time.sleep(wait)
                continue

            response.raise_for_status()
            return response
        except requests.RequestException as exc:
            if attempt == max_attempts - 1:
                raise
            wait = 2 ** attempt
            logger.warning("Request failed on %s (attempt %s), retry in %ss: %s", url, attempt + 1, wait, exc)
            time.sleep(wait)

    raise requests.RequestException(f"Failed after {max_attempts} attempts: {url}")


def get_ebay_token() -> str:
    """Return a cached eBay application token, refreshing it when expired."""
    now = time.time()
    cached = _TOKEN_CACHE.get("token")
    if cached and _TOKEN_CACHE.get("expires_at", 0) > now + 60:
        return cached

    client_id = os.environ.get("EBAY_CLIENT_ID", "")
    client_secret = os.environ.get("EBAY_CLIENT_SECRET", "")
    if not client_id or not client_secret:
        raise ValueError("Missing EBAY_CLIENT_ID or EBAY_CLIENT_SECRET environment variables")

    auth_str = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    headers = {
        "Authorization": f"Basic {auth_str}",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    data = {
        "grant_type": "client_credentials",
        "scope": "https://api.ebay.com/oauth/api_scope",
    }

    urls = _env_urls()
    logger.info("Requesting new eBay access token (environment=%s)", os.environ.get("EBAY_ENVIRONMENT", "SANDBOX"))
    response = _request_with_retry("POST", urls["auth"], headers=headers, data=data)
    payload = response.json()

    token = payload.get("access_token")
    expires_in = payload.get("expires_in", 7200)
    if not token:
        raise ValueError("eBay token response did not contain access_token")

    _TOKEN_CACHE["token"] = token
    _TOKEN_CACHE["expires_at"] = now + float(expires_in) - 60
    logger.info("eBay access token obtained, expires in %ss", expires_in)
    return token


def search_ebay_items(
    access_token: str,
    query: str,
    limit: int,
    offset: int,
) -> dict[str, Any]:
    """Search eBay items and return the raw JSON response."""
    urls = _env_urls()
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/json",
    }
    params = {
        "q": query,
        "limit": limit,
        "offset": offset,
        "filter": _PRICE_FILTER,
        "sort": _SORT,
    }

    response = _request_with_retry("GET", urls["browse"], headers=headers, params=params)
    return response.json()


def _parse_item(item: dict[str, Any]) -> dict[str, Any] | None:
    """Map a single eBay item summary to our internal product/price shape."""
    item_id = item.get("itemId")
    title = item.get("title")
    price = item.get("price", {})
    price_value = price.get("value")
    currency = price.get("currency") or "USD"

    if not item_id or not title or price_value is None:
        logger.debug("Skipping item with missing required fields: %s", item_id)
        return None

    try:
        price_decimal = Decimal(str(price_value))
    except InvalidOperation:
        logger.warning("Invalid price value for item %s: %s", item_id, price_value)
        return None

    seller = item.get("seller", {})
    seller_name = seller.get("username")
    feedback = seller.get("feedbackPercentage")
    seller_rating: Decimal | None = None
    if feedback is not None:
        try:
            r = Decimal(str(feedback))
            # eBay feedbackPercentage is 0-100; our seller_rating column is DECIMAL(3,2),
            # so store it as a 0-1 proportion to fit safely.
            if r > 1:
                r = r / 100
            seller_rating = r
        except InvalidOperation:
            seller_rating = None

    return {
        "source_id": str(item_id),
        "name": str(title),
        "price": price_decimal,
        "currency": str(currency),
        "seller_name": seller_name,
        "seller_rating": seller_rating,
        # Browse search summary does not expose review/rating/sold counts reliably.
        "rating": None,
        "review_count": None,
        "sold_count": None,
    }


def upsert_product(engine: Engine, product_data: dict[str, Any]) -> int:
    """Insert or update a product and return its primary key."""
    with engine.begin() as conn:
        result = conn.execute(
            text("SELECT id FROM produk WHERE source = :source AND source_id = :source_id"),
            {"source": _SOURCE, "source_id": product_data["source_id"]},
        )
        row = result.fetchone()

        if row:
            product_id = row[0]
            conn.execute(
                text(
                    "UPDATE produk SET "
                    "name = :name, seller_name = :seller_name, seller_rating = :seller_rating, "
                    "last_seen = NOW() WHERE id = :id"
                ),
                {
                    "id": product_id,
                    "name": product_data["name"],
                    "seller_name": product_data["seller_name"],
                    "seller_rating": product_data["seller_rating"],
                },
            )
            logger.debug("Updated product id=%s source_id=%s", product_id, product_data["source_id"])
        else:
            result = conn.execute(
                text(
                    "INSERT INTO produk (source, source_id, name, seller_name, seller_rating, first_seen, last_seen) "
                    "VALUES (:source, :source_id, :name, :seller_name, :seller_rating, NOW(), NOW())"
                ),
                {
                    "source": _SOURCE,
                    "source_id": product_data["source_id"],
                    "name": product_data["name"],
                    "seller_name": product_data["seller_name"],
                    "seller_rating": product_data["seller_rating"],
                },
            )
            product_id = result.lastrowid
            logger.debug("Inserted product id=%s source_id=%s", product_id, product_data["source_id"])

    return product_id


def insert_price_history(
    engine: Engine,
    product_id: int,
    price_data: dict[str, Any],
    fetch_batch: str,
) -> None:
    """Insert one price-history row for a product."""
    with engine.begin() as conn:
        conn.execute(
            text(
                "INSERT INTO histori_harga "
                "(product_id, price, currency, rating, review_count, sold_count, fetched_at, fetch_batch) "
                "VALUES (:product_id, :price, :currency, :rating, :review_count, :sold_count, NOW(), :fetch_batch)"
            ),
            {
                "product_id": product_id,
                "price": price_data["price"],
                "currency": price_data["currency"],
                "rating": price_data["rating"],
                "review_count": price_data["review_count"],
                "sold_count": price_data["sold_count"],
                "fetch_batch": fetch_batch,
            },
        )


def run_fetch(dry_run: bool = False) -> None:
    """Main entry point: fetch eBay items and persist them."""
    fetch_batch = str(uuid.uuid4())
    logger.info("Starting fetch for query=%s, batch=%s, dry_run=%s", _KEYWORD, fetch_batch, dry_run)

    engine: Engine | None = None
    if not dry_run:
        engine = get_connection()

    access_token = get_ebay_token()
    total_upserted = 0

    for page in range(_MAX_PAGES):
        offset = page * _LIMIT
        try:
            response = search_ebay_items(access_token, _KEYWORD, _LIMIT, offset)
        except requests.RequestException as exc:
            logger.error("Search failed at page %s (offset=%s): %s", page + 1, offset, exc)
            continue

        items = response.get("itemSummaries", []) or []
        logger.info("Fetched %s items from page %s (offset=%s)", len(items), page + 1, offset)

        if not items:
            break

        for item in items:
            parsed = _parse_item(item)
            if parsed is None:
                continue

            if dry_run:
                logger.info("Dry-run: would upsert source_id=%s price=%s %s", parsed["source_id"], parsed["price"], parsed["currency"])
                total_upserted += 1
                continue

            try:
                product_id = upsert_product(engine, parsed)
                insert_price_history(engine, product_id, parsed, fetch_batch)
                total_upserted += 1
                logger.info("Upserted product id=%s, inserted price history", product_id)
            except Exception as exc:  # noqa: BLE001
                logger.error("Failed to persist source_id=%s: %s", parsed["source_id"], exc)

        if page < _MAX_PAGES - 1:
            time.sleep(1)

    logger.info("Fetch complete. batch=%s total_processed=%s", fetch_batch, total_upserted)


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()
    run_fetch()
