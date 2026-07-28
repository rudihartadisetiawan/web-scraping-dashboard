"""Price-drop alerts and deal discovery."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine


def detect_price_drops(engine: Engine, days: int = 7, threshold_pct: float = 10.0) -> pd.DataFrame:
    """Find products where latest price dropped >threshold% vs average of last N days."""
    query = text(
        """
        WITH ranked AS (
            SELECT
                h.product_id,
                h.price,
                h.fetched_at,
                ROW_NUMBER() OVER (PARTITION BY h.product_id ORDER BY h.fetched_at DESC) AS rn
            FROM histori_harga h
            WHERE h.fetched_at >= DATE_SUB(NOW(), INTERVAL :days DAY)
        ),
        latest AS (
            SELECT product_id, price AS latest_price
            FROM ranked
            WHERE rn = 1
        ),
        avg_price AS (
            SELECT product_id, AVG(price) AS avg_price
            FROM ranked
            GROUP BY product_id
        )
        SELECT
            p.id AS product_id,
            p.name,
            ap.avg_price,
            l.latest_price,
            ((ap.avg_price - l.latest_price) / ap.avg_price) * 100 AS drop_pct,
            p.seller_name
        FROM produk p
        JOIN latest l ON l.product_id = p.id
        JOIN avg_price ap ON ap.product_id = p.id
        WHERE ((ap.avg_price - l.latest_price) / ap.avg_price) * 100 > :threshold_pct
        ORDER BY drop_pct DESC
        """
    )
    return pd.read_sql(
        query, engine, params={"days": days, "threshold_pct": threshold_pct}
    )


def get_top_deals(engine: Engine, limit: int = 10) -> pd.DataFrame:
    """Return top N products with biggest price drops, sorted by drop_pct DESC."""
    query = text(
        """
        WITH ranked AS (
            SELECT
                h.product_id,
                h.price,
                h.fetched_at,
                ROW_NUMBER() OVER (PARTITION BY h.product_id ORDER BY h.fetched_at DESC) AS rn,
                COUNT(*) OVER (PARTITION BY h.product_id) AS cnt
            FROM histori_harga h
        ),
        latest AS (
            SELECT product_id, price AS latest_price
            FROM ranked
            WHERE rn = 1 AND cnt > 1
        ),
        prev AS (
            SELECT product_id, price AS prev_price
            FROM ranked
            WHERE rn = 2
        )
        SELECT
            p.id AS product_id,
            p.name,
            p.seller_name,
            prev.prev_price,
            l.latest_price,
            ((prev.prev_price - l.latest_price) / prev.prev_price) * 100 AS drop_pct
        FROM produk p
        JOIN latest l ON l.product_id = p.id
        JOIN prev ON prev.product_id = p.id
        ORDER BY drop_pct DESC
        LIMIT :limit
        """
    )
    return pd.read_sql(query, engine, params={"limit": limit})
