"""Seed dummy sneakers data into the local MySQL dev database.

This script is intentionally hardcoded for local development only.
Production code must read credentials from environment variables.
"""

from __future__ import annotations

import random
import sys
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

# ponytail: allow running the script directly from the scraper folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import create_engine, text

# Hardcoded dev connection string — DO NOT USE IN PRODUCTION
DEV_DB_URL = "mysql+pymysql://root:@127.0.0.1:3306/price_monitor?charset=utf8mb4"

_SOURCE = "ebay"
_CATEGORY = "sneakers"
_CURRENCY = "USD"
_DAYS_HISTORY = 7
_DAYS_SINCE_FIRST_SEEN = 8

_PRODUCTS = [
    {"name": "Nike Air Max 90", "brand": "Nike"},
    {"name": "Adidas Ultraboost 22", "brand": "Adidas"},
    {"name": "New Balance 550", "brand": "New Balance"},
    {"name": "Vans Old Skool", "brand": "Vans"},
    {"name": "Converse Chuck Taylor All Star", "brand": "Converse"},
    {"name": "Puma Suede Classic", "brand": "Puma"},
    {"name": "Reebok Classic Leather", "brand": "Reebok"},
    {"name": "Asics Gel-Kayano 29", "brand": "Asics"},
    {"name": "Jordan Air 1 Low", "brand": "Jordan"},
    {"name": "Skechers D'Lites", "brand": "Skechers"},
    {"name": "Nike Dunk Low", "brand": "Nike"},
    {"name": "Adidas Stan Smith", "brand": "Adidas"},
    {"name": "New Balance 574", "brand": "New Balance"},
]

_SELLERS = [
    "shoe_deals",
    "sneaker_head",
    "retail_zone",
    "kickz_corner",
    "urban_kicks",
    "sole_supply",
    "top_sneaks",
]

_DROP_PRODUCT_NAMES = ["Nike Air Max 90", "Adidas Ultraboost 22", "Jordan Air 1 Low"]


def _rnd_pct(low: float, high: float) -> float:
    return random.uniform(low, high)


def _generate_price_series(base_price: float, force_drop: bool) -> list[float]:
    """Generate 7 daily prices. If force_drop, ensure last price is >10% below day -4."""
    prices = [round(base_price, 2)]
    for _ in range(_DAYS_HISTORY - 1):
        change = _rnd_pct(-0.05, 0.05)
        prices.append(round(max(10.0, prices[-1] * (1 + change)), 2))

    if force_drop:
        # Force a significant cumulative drop over the last 3 days (~30%)
        # so it is detectable against both the trailing average and the price 3 days ago.
        prices[-3] = round(prices[-4] * 0.90, 2)
        prices[-2] = round(prices[-3] * 0.88, 2)
        prices[-1] = round(prices[-2] * 0.85, 2)

    return prices


def _maybe_null(value):
    return None if random.random() < 0.25 else value


def seed(engine_url: str) -> dict[str, int]:
    engine = create_engine(engine_url, pool_pre_ping=True)
    now = datetime.now()
    first_seen = now - timedelta(days=_DAYS_SINCE_FIRST_SEEN)
    last_seen = now - timedelta(days=1)

    # One fetch batch UUID per history day
    batch_dates = [now - timedelta(days=days) for days in range(_DAYS_HISTORY, 0, -1)]
    batch_map = {dt.date(): str(uuid.uuid4()) for dt in batch_dates}

    with engine.begin() as conn:
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 0"))
        conn.execute(text("TRUNCATE TABLE histori_harga"))
        conn.execute(text("TRUNCATE TABLE produk"))
        conn.execute(text("SET FOREIGN_KEY_CHECKS = 1"))
        print("[OK] Truncated histori_harga and produk")

        product_count = 0
        history_count = 0

        for idx, product in enumerate(_PRODUCTS, start=1):
            source_id = f"SNKR-{idx:03d}"
            seller_name = random.choice(_SELLERS)
            seller_rating = round(random.uniform(0.85, 0.99), 2)
            base_price = random.uniform(25.0, 280.0)
            force_drop = product["name"] in _DROP_PRODUCT_NAMES

            result = conn.execute(
                text(
                    "INSERT INTO produk "
                    "(source, source_id, name, category, seller_name, seller_rating, first_seen, last_seen) "
                    "VALUES (:source, :source_id, :name, :category, :seller_name, :seller_rating, :first_seen, :last_seen)"
                ),
                {
                    "source": _SOURCE,
                    "source_id": source_id,
                    "name": product["name"],
                    "category": _CATEGORY,
                    "seller_name": seller_name,
                    "seller_rating": Decimal(str(seller_rating)),
                    "first_seen": first_seen,
                    "last_seen": last_seen,
                },
            )
            product_id = result.lastrowid
            product_count += 1

            prices = _generate_price_series(base_price, force_drop)
            for batch_dt, price in zip(batch_dates, prices):
                rating = _maybe_null(round(random.uniform(3.5, 5.0), 1))
                review_count = _maybe_null(random.randint(10, 500))
                sold_count = _maybe_null(random.randint(5, 200))

                conn.execute(
                    text(
                        "INSERT INTO histori_harga "
                        "(product_id, price, currency, rating, review_count, sold_count, fetched_at, fetch_batch) "
                        "VALUES (:product_id, :price, :currency, :rating, :review_count, :sold_count, :fetched_at, :fetch_batch)"
                    ),
                    {
                        "product_id": product_id,
                        "price": Decimal(str(price)),
                        "currency": _CURRENCY,
                        "rating": Decimal(str(rating)) if rating is not None else None,
                        "review_count": review_count,
                        "sold_count": sold_count,
                        "fetched_at": batch_dt,
                        "fetch_batch": batch_map[batch_dt.date()],
                    },
                )
                history_count += 1

            drop_note = " [DROP]" if force_drop else ""
            print(f"[OK] Inserted product {source_id}: {product['name']} - {len(prices)} rows{drop_note}")

    return {"products": product_count, "history_rows": history_count}


if __name__ == "__main__":
    summary = seed(DEV_DB_URL)
    print("\n=== Summary ===")
    print(f"Products inserted: {summary['products']}")
    print(f"Price history rows inserted: {summary['history_rows']}")
