"""Summary statistics for the dataset."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine


def get_summary_stats(engine: Engine) -> dict:
    """Return dict with high-level dataset statistics."""
    products = pd.read_sql(
        text("SELECT COUNT(*) AS total FROM produk WHERE is_active = TRUE"),
        engine,
    ).iloc[0]["total"]

    price_stats = pd.read_sql(
        text("SELECT price FROM histori_harga"),
        engine,
    )

    date_range = pd.read_sql(
        text("SELECT MIN(fetched_at) AS first, MAX(fetched_at) AS last FROM histori_harga"),
        engine,
    ).iloc[0]

    products_with_drops = pd.read_sql(
        text(
            """
            WITH latest AS (
                SELECT product_id, price,
                       ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY fetched_at DESC) AS rn
                FROM histori_harga
            ),
            three_days_ago AS (
                SELECT product_id, price,
                       ROW_NUMBER() OVER (
                           PARTITION BY product_id
                           ORDER BY CASE WHEN fetched_at <= DATE_SUB(NOW(), INTERVAL 3 DAY) THEN 0 ELSE 1 END,
                                    fetched_at DESC
                       ) AS rn
                FROM histori_harga
            )
            SELECT COUNT(DISTINCT l.product_id) AS drop_count
            FROM latest l
            JOIN three_days_ago p ON p.product_id = l.product_id AND p.rn = 1
            WHERE ((p.price - l.price) / p.price) * 100 > 10
            """
        ),
        engine,
    ).iloc[0]["drop_count"]

    top_category = pd.read_sql(
        text(
            "SELECT category, COUNT(*) AS cnt FROM produk "
            "WHERE category IS NOT NULL GROUP BY category ORDER BY cnt DESC LIMIT 1"
        ),
        engine,
    )

    return {
        "total_products": int(products),
        "avg_price": float(price_stats["price"].mean()) if not price_stats.empty else None,
        "median_price": float(price_stats["price"].median()) if not price_stats.empty else None,
        "total_price_records": int(price_stats.shape[0]),
        "date_range_first": date_range["first"],
        "date_range_last": date_range["last"],
        "products_with_drops": int(products_with_drops),
        "top_category": top_category.iloc[0]["category"] if not top_category.empty else None,
    }
