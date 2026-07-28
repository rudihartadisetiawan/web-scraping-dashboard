"""Ranking helpers: value-for-money and seller price comparison."""

from __future__ import annotations

import pandas as pd
from sqlalchemy import text
from sqlalchemy.engine import Engine


def value_for_money_rank(engine: Engine, limit: int = 20) -> pd.DataFrame:
    """Rank products by price/rating ratio (lower price + higher rating = better value)."""
    query = text(
        """
        WITH latest AS (
            SELECT
                h.product_id,
                h.price,
                h.rating,
                ROW_NUMBER() OVER (PARTITION BY h.product_id ORDER BY h.fetched_at DESC) AS rn
            FROM histori_harga h
        )
        SELECT
            p.id AS product_id,
            p.name,
            l.price,
            l.rating,
            (l.price / NULLIF(l.rating, 0)) AS value_score,
            p.seller_name
        FROM produk p
        JOIN latest l ON l.product_id = p.id AND l.rn = 1
        WHERE l.rating IS NOT NULL
        ORDER BY value_score ASC
        LIMIT :limit
        """
    )
    return pd.read_sql(query, engine, params={"limit": limit})


def seller_price_comparison(engine: Engine, product_name_keyword: str) -> pd.DataFrame:
    """For a given keyword, compare prices across sellers for similar products."""
    query = text(
        """
        WITH latest AS (
            SELECT
                h.product_id,
                h.price,
                h.fetched_at,
                ROW_NUMBER() OVER (PARTITION BY h.product_id ORDER BY h.fetched_at DESC) AS rn
            FROM histori_harga h
        )
        SELECT
            p.id AS product_id,
            p.name,
            p.seller_name,
            p.seller_rating,
            l.price,
            l.fetched_at
        FROM produk p
        JOIN latest l ON l.product_id = p.id AND l.rn = 1
        WHERE p.name LIKE :keyword
        ORDER BY l.price ASC
        """
    )
    keyword = f"%{product_name_keyword}%"
    return pd.read_sql(query, engine, params={"keyword": keyword})
