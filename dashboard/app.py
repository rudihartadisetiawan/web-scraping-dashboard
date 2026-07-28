"""Sneaker Price Monitor — Streamlit dashboard.

Visual identity: charcoal base + signal-lime accent, Bebas Neue for
big numerals, signature price-drop ticker. Built for international reseller
/ dropshipper audience.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Make sibling packages importable when running from dashboard/
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from scraper.db import get_connection  # noqa: E402

# analysis/ is built in parallel; degrade gracefully if not ready yet.
try:
    from analysis.trends import get_all_product_trends
    from analysis.alerts import get_top_deals
    from analysis.rankings import value_for_money_rank
    from analysis.summary import get_summary_stats
except ImportError:  # ponytail: analysis module not ready yet
    get_all_product_trends = None
    get_top_deals = None
    value_for_money_rank = None
    get_summary_stats = None


# --------------------------------------------------------------------------- #
# Design tokens
# --------------------------------------------------------------------------- #
BG_PRIMARY = "#1a1d23"
BG_SECONDARY = "#242830"
BG_TERTIARY = "#2d323c"
TEXT_PRIMARY = "#e8e8ec"
TEXT_SECONDARY = "#9195a0"
VOLT = "#ccff00"        # signature accent — signal lime
RED = "#ff4444"         # price drops / negative
GREEN = "#00e676"       # price rises / positive
BORDER = "#3a3f4b"

FONT_BODY = "Inter"
FONT_DISPLAY = "Bebas Neue"

_CURRENCY = "USD"


# --------------------------------------------------------------------------- #
# CSS
# --------------------------------------------------------------------------- #
def _css() -> None:
    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family={FONT_BODY.replace(" ", "+")}:wght@400;500;600;700&family={FONT_DISPLAY.replace(" ", "+")}&family=JetBrains+Mono:wght@500&display=swap');

        /* ---- shell ---- */
        .stApp {{
            background-color: {BG_PRIMARY};
            background-image:
                radial-gradient(circle at 1px 1px, rgba(255,255,255,0.025) 1px, transparent 0);
            background-size: 22px 22px;
            color: {TEXT_PRIMARY};
            font-family: '{FONT_BODY}', sans-serif;
        }}
        /* subtle tread/shoeprint texture band */
        .stApp::before {{
            content: "";
            position: fixed; inset: 0;
            background-image: repeating-linear-gradient(
                115deg, transparent 0 38px, rgba(204,255,0,0.018) 38px 40px);
            pointer-events: none; z-index: 0;
        }}

        h1, h2, h3, .display {{ font-family: '{FONT_DISPLAY}', sans-serif; letter-spacing: 1px; }}

        /* ---- header ---- */
        .dash-header {{
            display: flex; align-items: baseline; gap: 14px;
            padding: 6px 0 2px 0;
        }}
        .dash-mark {{
            font-family: '{FONT_DISPLAY}', sans-serif;
            font-size: 42px; line-height: 1; color: {VOLT};
            letter-spacing: 2px;
        }}
        .dash-title {{
            font-family: '{FONT_DISPLAY}', sans-serif;
            font-size: 30px; line-height: 1; color: {TEXT_PRIMARY};
            letter-spacing: 2px;
        }}
        .dash-sub {{
            color: {TEXT_SECONDARY}; font-size: 13px; margin-left: auto;
            font-family: 'JetBrains Mono', monospace;
        }}

        /* ---- signature ticker ---- */
        .ticker {{
            background: {BG_SECONDARY};
            border: 1px solid {BORDER};
            border-left: 3px solid {VOLT};
            border-radius: 6px;
            overflow: hidden;
            margin: 10px 0 18px 0;
            position: relative;
        }}
        .ticker-label {{
            position: absolute; left: 0; top: 0; bottom: 0;
            background: {VOLT}; color: #0a0a0a;
            font-family: '{FONT_DISPLAY}', sans-serif; letter-spacing: 2px;
            font-size: 14px; padding: 0 12px;
            display: flex; align-items: center; z-index: 2;
        }}
        .ticker-track {{
            display: flex; gap: 28px; padding: 9px 12px 9px 96px;
            white-space: nowrap;
            font-family: 'JetBrains Mono', monospace; font-size: 13px;
            animation: tickscroll 38s linear infinite;
        }}
        .ticker-item .tk-name {{ color: {TEXT_PRIMARY}; }}
        .ticker-item .tk-drop {{ color: {RED}; font-weight: 600; }}
        .ticker-item .tk-price {{ color: {TEXT_SECONDARY}; }}
        @keyframes tickscroll {{
            0%   {{ transform: translateX(0); }}
            100% {{ transform: translateX(-50%); }}
        }}

        /* ---- metric cards ---- */
        div[data-testid="stMetric"] {{
            background: {BG_SECONDARY};
            border: 1px solid {BORDER};
            border-radius: 8px;
            padding: 16px 18px 14px 18px !important;
            box-shadow: 0 1px 0 rgba(0,0,0,0.25);
        }}
        div[data-testid="stMetric"] label {{
            color: {TEXT_SECONDARY};
            font-size: 11px; font-weight: 600;
            letter-spacing: 1.2px; text-transform: uppercase;
            font-family: '{FONT_BODY}', sans-serif;
        }}
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] {{
            font-family: '{FONT_DISPLAY}', sans-serif;
            font-size: 40px; line-height: 1.05; color: {TEXT_PRIMARY};
            letter-spacing: 1px;
        }}
        div[data-testid="stMetric"] div[data-testid="stMetricDelta"] {{
            font-family: 'JetBrains Mono', monospace; font-size: 12px;
        }}
        /* delta colors */
        div[data-testid="stMetric"] div[data-testid="stMetricDelta"] svg {{ display: none; }}

        /* ---- section headings ---- */
        .sec-h {{
            font-family: '{FONT_DISPLAY}', sans-serif;
            font-size: 22px; letter-spacing: 2px; color: {TEXT_PRIMARY};
            border-left: 3px solid {VOLT}; padding-left: 10px;
            margin: 22px 0 10px 0;
        }}
        .sec-sub {{ color: {TEXT_SECONDARY}; font-size: 12px; margin: -6px 0 10px 13px; }}

        /* ---- sidebar ---- */
        section[data-testid="stSidebar"] {{
            background-color: {BG_SECONDARY};
            border-right: 1px solid {BORDER};
        }}
        section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label {{
            color: {TEXT_SECONDARY};
        }}
        .side-brand {{
            font-family: '{FONT_DISPLAY}', sans-serif; font-size: 26px;
            color: {VOLT}; letter-spacing: 2px; line-height: 1;
        }}
        .side-tag {{ color: {TEXT_SECONDARY}; font-size: 11px; letter-spacing: 1px; text-transform: uppercase; }}

        /* ---- buttons / sliders ---- */
        .stSlider > div > div > div {{ background: {BORDER}; }}
        .stSlider span[data-baseweb="slider-thumb"] {{
            border-color: {VOLT}; background: {VOLT}; height: 16px; width: 16px;
        }}
        .stSlider span[data-baseweb="slider-track"] {{ background: {VOLT} !important; }}
        .stSelectbox, .stMultiSelect [data-baseweb="select"] > div {{
            background: {BG_TERTIARY}; border-color: {BORDER};
        }}

        /* ---- dataframes / tables ---- */
        .stDataFrame, .stTable {{
            background: transparent;
        }}
        table {{ border-collapse: collapse; width: 100%; }}
        th {{ color: {VOLT} !important; font-family: '{FONT_BODY}', sans-serif;
             font-size: 11px; letter-spacing: 1px; text-transform: uppercase; }}
        .deal-row-hot {{ background: rgba(255,68,68,0.10) !important; }}
        .rank-badge {{
            display: inline-flex; align-items: center; justify-content: center;
            width: 26px; height: 26px; border-radius: 50%;
            background: {BG_TERTIARY}; color: {VOLT};
            font-family: '{FONT_DISPLAY}', sans-serif; font-size: 15px;
            border: 1px solid {BORDER};
        }}
        .rank-badge.top {{ background: {VOLT}; color: #0a0a0a; border-color: {VOLT}; }}

        /* ---- empty state ---- */
        .empty {{
            border: 1px dashed {BORDER}; border-radius: 8px;
            padding: 28px; text-align: center; color: {TEXT_SECONDARY};
            font-size: 14px; background: {BG_SECONDARY};
        }}
        .empty b {{ color: {TEXT_PRIMARY}; font-family: '{FONT_DISPLAY}', sans-serif;
                   letter-spacing: 1px; font-size: 18px; display:block; margin-bottom: 6px; }}

        /* hide streamlit chrome */
        #MainMenu {{ visibility: hidden; }}
        footer {{ visibility: hidden; }}
        </style>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- #
# Data access (cached)
# --------------------------------------------------------------------------- #
@st.cache_data(ttl=300, show_spinner=False)
def _engine():
    return get_connection()


@st.cache_data(ttl=300, show_spinner="Pulling latest sneaker prices…")
def _trends():
    if get_all_product_trends is None:
        return pd.DataFrame()
    return get_all_product_trends(_engine())


@st.cache_data(ttl=300, show_spinner=False)
def _deals(limit: int):
    if get_top_deals is None:
        return pd.DataFrame()
    return get_top_deals(_engine(), limit=limit)


@st.cache_data(ttl=300, show_spinner=False)
def _ranking(limit: int):
    if value_for_money_rank is None:
        return pd.DataFrame()
    return value_for_money_rank(_engine(), limit=limit)


@st.cache_data(ttl=300, show_spinner=False)
def _summary():
    if get_summary_stats is None:
        return {}
    return get_summary_stats(_engine())


@st.cache_data(ttl=300, show_spinner=False)
def _price_bounds():
    """Min/max price across history for the slider range."""
    engine = _engine()
    from sqlalchemy import text
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT MIN(price) AS lo, MAX(price) AS hi FROM histori_harga")
        ).fetchone()
    if row is None or row.lo is None:
        return 0.0, 500.0
    return float(row.lo), float(row.hi)


@st.cache_data(ttl=300, show_spinner=False)
def _date_bounds():
    engine = _engine()
    from sqlalchemy import text
    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT MIN(fetched_at) AS lo, MAX(fetched_at) AS hi FROM histori_harga")
        ).fetchone()
    if row is None or row.lo is None:
        return pd.Timestamp.now() - pd.Timedelta(days=30), pd.Timestamp.now()
    return pd.Timestamp(row.lo), pd.Timestamp(row.hi)


# --------------------------------------------------------------------------- #
# UI pieces
# --------------------------------------------------------------------------- #
def _header() -> None:
    st.markdown(
        f"""
        <div class="dash-header">
            <span class="dash-mark">SNKR//</span>
            <span class="dash-title">PRICE MONITOR</span>
            <span class="dash-sub">live sneaker marketplace intelligence</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _ticker(deals: pd.DataFrame) -> None:
    if deals.empty:
        return
    top = deals.head(12)
    items = []
    for _, r in top.iterrows():
        name = str(r.get("name", "?"))[:34]
        drop = r.get("drop_pct", 0)
        cur = r.get("latest_price", r.get("price", 0))
        try:
            drop = float(drop)
        except (TypeError, ValueError):
            drop = 0.0
        try:
            cur = float(cur)
        except (TypeError, ValueError):
            cur = 0.0
        items.append(
            f'<span class="ticker-item">'
            f'<span class="tk-name">{name}</span> '
            f'<span class="tk-drop">▼ {drop:.1f}%</span> '
            f'<span class="tk-price">${cur:,.0f}</span></span>'
        )
    # duplicate for seamless loop
    track = "".join(items) + "".join(items)
    st.markdown(
        f"""
        <div class="ticker">
            <div class="ticker-label">DROPS</div>
            <div class="ticker-track">{track}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _empty(msg: str, detail: str = "") -> None:
    st.markdown(
        f'<div class="empty"><b>{msg}</b>{detail}</div>',
        unsafe_allow_html=True,
    )


def _fmt_money(v) -> str:
    try:
        return f"${float(v):,.0f}"
    except (TypeError, ValueError):
        return "—"


def _summary_row(stats: dict, deals: pd.DataFrame, threshold: float,
                 avg_delta: float | None = None) -> None:
    total = stats.get("total_products", 0)
    avg = stats.get("avg_price", 0)
    median = stats.get("median_price", 0)
    active_deals = int((deals.get("drop_pct", pd.Series(dtype=float)) > threshold).sum()) if not deals.empty else 0

    # trend delta for avg (computed in main from trends)
    delta_str = f"{avg_delta:+,.2f}" if avg_delta is not None else None

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("PRODUCTS TRACKED", f"{int(total):,}")
    c2.metric("AVG PRICE", _fmt_money(avg), delta=delta_str,
              delta_color="inverse")  # price up = bad for buyer → red
    c3.metric("MEDIAN PRICE", _fmt_money(median))
    c4.metric("ACTIVE DEALS", f"{active_deals}",
              help=f"Products that dropped more than {threshold:.0f}% vs their previous price.")


def _trend_chart(trends: pd.DataFrame) -> None:
    st.markdown('<div class="sec-h">PRICE TREND</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sec-sub">Compare up to 5 sneakers head-to-head, or isolate one.</div>',
        unsafe_allow_html=True,
    )
    if trends.empty:
        _empty("No price history yet",
               "Once the daily fetch has run for a few days, sneaker price lines will plot here.")
        return

    # Expect columns: name, fetched_at, price (analysis contract)
    name_col = "name" if "name" in trends.columns else trends.columns[0]
    date_col = "fetched_at" if "fetched_at" in trends.columns else "date"
    price_col = "price" if "price" in trends.columns else trends.columns[-1]

    products = sorted(trends[name_col].dropna().unique().tolist())
    sel = st.selectbox(
        "Sneaker in focus", ["— Compare top 5 —"] + products,
        key="trend_focus", label_visibility="collapsed")
    if sel == "— Compare top 5 —":
        # pick 5 with most data points
        top5 = (trends.groupby(name_col)[price_col].count()
                .sort_values(ascending=False).head(5).index.tolist())
        sub = trends[trends[name_col].isin(top5)]
    else:
        sub = trends[trends[name_col] == sel]

    wide = sub.pivot_table(index=date_col, columns=name_col, values=price_col, aggfunc="last")
    wide.index = pd.to_datetime(wide.index)
    wide = wide.sort_index()
    st.line_chart(wide, height=320, color=[VOLT, RED, GREEN, "#4a9eff", "#ff9e3d"])


def _deals_table(deals: pd.DataFrame, threshold: float) -> None:
    st.markdown('<div class="sec-h">TOP DEALS</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="sec-sub">Biggest price drops right now — rows shaded red beat your {threshold:.0f}% threshold.</div>',
        unsafe_allow_html=True,
    )
    if deals.empty:
        _empty("No deals detected",
               "Drop the threshold slider, or wait for the next fetch to surface price moves.")
        return

    # normalize column names from analysis contract
    col_map = {
        "name": "Product", "seller_name": "Seller",
        "prev_price": "Prev", "latest_price": "Now",
        "drop_pct": "Drop %", "value_score": "Value",
    }
    show = deals.rename(columns={k: v for k, v in col_map.items() if k in deals.columns})
    want = ["Product", "Seller", "Prev", "Now", "Drop %", "Value"]
    show = show[[c for c in want if c in show.columns]]
    if "Drop %" in show.columns:
        show = show.sort_values("Drop %", ascending=False)
        show["Drop %"] = show["Drop %"].map(lambda v: f"▼ {float(v):.1f}%")
    for c in ("Prev", "Now"):
        if c in show.columns:
            show[c] = show[c].map(_fmt_money)
    if "Value" in show.columns:
        show["Value"] = show["Value"].map(lambda v: f"{float(v):.2f}" if pd.notna(v) else "—")

    # highlight hot rows
    def _style(row):
        # parse the numeric drop back out of the formatted string
        try:
            val = float(str(row["Drop %"]).replace("▼", "").replace("%", "").strip())
        except (ValueError, KeyError):
            val = 0
        if val > threshold:
            return [f"background-color: rgba(255,68,68,0.10)"] * len(row)
        return [""] * len(row)

    st.dataframe(show.style.apply(_style, axis=1), use_container_width=True,
                 hide_index=True, height=320)


def _ranking_table(ranking: pd.DataFrame) -> None:
    st.markdown('<div class="sec-h">VALUE-FOR-MONEY RANKING</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sec-sub">Best price-to-rating ratio across the catalogue.</div>',
        unsafe_allow_html=True,
    )
    if ranking.empty:
        _empty("Ranking not ready",
               "Value scores appear once ratings and prices are both collected.")
        return

    col_map = {
        "name": "Product", "price": "Price",
        "rating": "Rating", "value_score": "Value",
        "seller_name": "Seller",
    }
    show = ranking.rename(columns={k: v for k, v in col_map.items() if k in ranking.columns})
    show = show.reset_index(drop=True)
    show.insert(0, "#", range(1, len(show) + 1))
    if "Price" in show.columns:
        show["Price"] = show["Price"].map(_fmt_money)
    if "Rating" in show.columns:
        show["Rating"] = show["Rating"].map(lambda v: f"{float(v):.2f}★" if pd.notna(v) else "—")
    if "Value" in show.columns:
        show["Value"] = show["Value"].map(lambda v: f"{float(v):.2f}" if pd.notna(v) else "—")
    st.dataframe(show, use_container_width=True, hide_index=True, height=360)


# --------------------------------------------------------------------------- #
# Sidebar
# --------------------------------------------------------------------------- #
def _sidebar() -> dict:
    with st.sidebar:
        st.markdown('<div class="side-brand">SNKR//</div>', unsafe_allow_html=True)
        st.markdown('<div class="side-tag">price monitor · v1</div>', unsafe_allow_html=True)
        st.write("")
        st.markdown("**FILTERS**")

        category = st.selectbox("Category", ["sneakers"], key="f_category")

        try:
            lo, hi = _price_bounds()
        except Exception:
            lo, hi = 0.0, 500.0
        if lo == hi:
            hi = lo + 1
        price_range = st.slider(
            "Price range", float(lo), float(hi),
            (float(lo), float(hi)), step=max(1.0, (hi - lo) / 100), key="f_price")

        try:
            dlo, dhi = _date_bounds()
        except Exception:
            dlo = pd.Timestamp.now() - pd.Timedelta(days=30)
            dhi = pd.Timestamp.now()
        date_range = st.date_input(
            "Date range", value=(dlo.date(), dhi.date()), key="f_date")

        threshold = st.slider(
            "Price drop threshold (%)", 0, 50, 10, step=1, key="f_threshold",
            help="Flag a sneaker as a deal when its price falls this far below its recent average.")

        st.write("")
        st.markdown(
            f'<div class="side-tag">data: eBay · refreshed every 5 min in-session</div>',
            unsafe_allow_html=True)
    return {
        "category": category, "price_range": price_range,
        "date_range": date_range, "threshold": float(threshold),
    }


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    st.set_page_config(
        page_title="Sneaker Price Monitor",
        page_icon="👟",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _css()
    _header()

    filters = _sidebar()
    threshold = filters["threshold"]

    # ---- load (cached) ----
    try:
        stats = _summary()
        deals = _deals(limit=50)
        trends = _trends()
        ranking = _ranking(limit=20)
    except Exception as exc:  # ponytail: DB not wired yet → friendly empty state
        _empty("Dashboard waiting for data",
               f"The MySQL backend isn't reachable yet ({type(exc).__name__}). "
               "Once the scraper has run, prices populate here automatically.")
        _ticker(pd.DataFrame())
        return

    # attach value_score from ranking into deals for the Value column
    if (not deals.empty and not ranking.empty
            and "product_id" in deals.columns and "product_id" in ranking.columns
            and "value_score" in ranking.columns):
        deals = deals.merge(
            ranking[["product_id", "value_score"]].rename(columns={"value_score": "value_score"}),
            on="product_id", how="left")

    _ticker(deals)

    # avg price trend: compare mean of latest fetch day vs previous fetch day
    avg_delta = None
    if not trends.empty and "fetched_at" in trends.columns and "price" in trends.columns:
        try:
            by_day = (trends.assign(fetched_at=pd.to_datetime(trends["fetched_at"]))
                      .groupby(trends["fetched_at"].dt.date)["price"].mean().sort_index())
            if len(by_day) >= 2:
                avg_delta = float(by_day.iloc[-1] - by_day.iloc[-2])
        except Exception:
            avg_delta = None

    # A. summary
    _summary_row(stats, deals, threshold, avg_delta=avg_delta)

    # B + C. trend (wide) | deals (narrow)
    left, right = st.columns([3, 2])
    with left:
        _trend_chart(trends)
    with right:
        _deals_table(deals, threshold)

    # D. ranking full width
    _ranking_table(ranking)

    # footer note
    st.markdown(
        f'<div class="sec-sub" style="text-align:right;margin-top:18px;">'
        f'SNKR//PRICE MONITOR · portfolio build · all prices in {_currency()}</div>',
        unsafe_allow_html=True)


def _currency() -> str:
    return os.environ.get("DISPLAY_CURRENCY", _CURRENCY)


if __name__ == "__main__":
    main()