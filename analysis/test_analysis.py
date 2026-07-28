"""Smoke-test script for the analysis package."""

from __future__ import annotations

import sys
from pathlib import Path

from dotenv import load_dotenv

# ponytail: allow running the script directly from the analysis folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis.alerts import detect_price_drops, get_top_deals
from analysis.rankings import seller_price_comparison, value_for_money_rank
from analysis.summary import get_summary_stats
from analysis.trends import get_all_product_trends, get_price_trend
from scraper.db import get_connection
from sqlalchemy import text


def main() -> None:
    load_dotenv()
    engine = get_connection()

    print("=== Summary Stats ===")
    print(get_summary_stats(engine))

    print("\n=== Price Trend (first product) ===")
    with engine.connect() as conn:
        first_id = conn.execute(text("SELECT id FROM produk LIMIT 1")).scalar()
    print(get_price_trend(engine, product_id=first_id, days=30).head())

    print("\n=== All Product Trends ===")
    print(get_all_product_trends(engine, days=30).head())

    print("\n=== Price Drops (>10% over 7 days) ===")
    drops = detect_price_drops(engine, days=7, threshold_pct=10.0)
    print(drops.head())

    print("\n=== Top Deals ===")
    print(get_top_deals(engine, limit=10).head())

    print("\n=== Value For Money Rank ===")
    print(value_for_money_rank(engine, limit=10).head())

    print("\n=== Seller Price Comparison (Nike) ===")
    print(seller_price_comparison(engine, product_name_keyword="Nike").head())


if __name__ == "__main__":
    main()
