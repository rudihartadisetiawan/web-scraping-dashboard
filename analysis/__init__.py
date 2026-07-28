"""Analysis package for price trends, alerts, rankings, and summary statistics."""

from analysis.alerts import detect_price_drops, get_top_deals
from analysis.rankings import seller_price_comparison, value_for_money_rank
from analysis.summary import get_summary_stats
from analysis.trends import get_all_product_trends, get_price_trend

__all__ = [
    "detect_price_drops",
    "get_all_product_trends",
    "get_price_trend",
    "get_summary_stats",
    "get_top_deals",
    "seller_price_comparison",
    "value_for_money_rank",
]
