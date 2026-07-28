"""Price trend helpers."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine


def get_price_trend(engine: Engine, product_id: int, days: int = 30) -> pd.DataFrame:
    """Return time-series price + timestamp for one product."""
    query = text(
        "SELECT fetched_at, price "
        "FROM histori_harga "
        "WHERE product_id = :product_id AND fetched_at >= DATE_SUB(NOW(), INTERVAL :days DAY) "
        "ORDER BY fetched_at"
    )
    return pd.read_sql(query, engine, params={"product_id": product_id, "days": days})


def get_all_product_trends(engine: Engine, days: int = 30) -> pd.DataFrame:
    """Return price trends for all active products."""
    query = text(
        "SELECT p.id AS product_id, p.name, p.seller_name, h.fetched_at, h.price "
        "FROM produk p "
        "JOIN histori_harga h ON h.product_id = p.id "
        "WHERE p.is_active = TRUE "
        "  AND h.fetched_at >= DATE_SUB(NOW(), INTERVAL :days DAY) "
        "ORDER BY p.id, h.fetched_at"
    )
    return pd.read_sql(query, engine, params={"days": days})
