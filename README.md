# Sneaker Price Monitor — Global Marketplace Price & Trend Tracker

**Live dashboard** for monitoring sneaker prices on eBay — built for international resellers and dropshippers who need reliable, daily-updated pricing intelligence.

> *Portfolio project. Live demo: [Streamlit Cloud link coming soon]*

---

## What This Solves

Resellers and dropshippers compete on pricing. Prices on eBay shift daily — a seller drops a listing, a promo expires, a competitor undercuts. Manually tracking these moves across dozens of products is a time-sink.

This dashboard automates it:

1. **Daily price snapshots** via the official eBay Browse API — stable, TOS-compliant, no proxy needed.
2. **Time-series history** so you can see how prices trend over days, not just today's number.
3. **Deal detection** — flag products whose price dropped below their recent average.
4. **Value-for-money ranking** — sort the catalog by price-to-rating ratio so you spot underpriced inventory instantly.
5. **Seller comparison** — compare prices for the same product across different eBay sellers.

---

## Architecture

```
eBay Browse API (scheduled daily)
        │
        ▼
   [GitHub Actions cron]  ──fetch + upsert──▶  MySQL (cloud-hosted)
                                                       │
                                                       ▼
                                              [Streamlit dashboard]
                                              queries via SQLAlchemy
                                              pandas for on-the-fly analysis
```

### Key Technical Decisions

| Decision | Why |
|---|---|
| **API-first (eBay Browse API)** | Reliability over "hard scrape." eBay's official API is free for moderate volume, has clean structured JSON, and won't get blocked. Portfolios win on bulletproof data pipelines, not on scraping heroics. |
| **MySQL hosted (not SQLite)** | GitHub Actions runner and Streamlit Cloud are separate machines. Both need to read/write to the same DB. SQLite can't handle multi-environment access. A cloud MySQL instance solves this cleanly. |
| **Connection pooling (SQLAlchemy)** | Serverless environments (GH Actions, Streamlit Cloud) can leak connections without pooling. `pool_pre_ping=True` ensures stale connections are detected and re-established. |
| **Append-only history, never overwrite** | Every daily fetch inserts new `histori_harga` rows with a batch UUID. Old data is never touched. Reproducible audit trail, and time-series queries stay fast with composite indexes. |
| **GitHub Actions scheduler** | Free, reliable, and transparent. The workflow runs at 06:00 UTC daily. No separate VPS or cron server needed. |

---

## Tech Stack

| Layer | Tool |
|---|---|
| Data collection | Python 3.12, `requests` (eBay Browse API) |
| Storage | MySQL (Alibaba Cloud PolarDB free tier — MySQL 100% compatible) |
| Scheduling | GitHub Actions |
| Analysis | `pandas` + parameterized SQL |
| Dashboard | `streamlit` with custom CSS design tokens |
| Deployment | Streamlit Community Cloud |

---

## Features

- **Filter** by price range, date range, and drop threshold
- **Summary metric row** — products tracked, average price (+ day-over-day delta), median, active deals
- **Price trend chart** — compare up to 5 sneakers on one line chart, or focus on one
- **Animated price-drop ticker** — scrolling feed of the biggest drops (signature visual element)
- **Top Deals table** — rows exceeding your drop threshold shaded red
- **Value-for-Money ranking** — full catalog ranked by price ÷ rating ratio
- **Dark charcoal theme** with signal-lime accent, Bebas Neue typography, custom styling throughout

---

## Project Structure

```
scraper/        — eBay API client, DB connection, upsert logic, dummy seed data
analysis/       — pandas query modules (trends, alerts, rankings, summary)
dashboard/      — Streamlit app with custom design tokens and CSS
data/           — placeholder for exported artifacts
.github/        — CI/CD: daily fetch workflow
```

---

## Running Locally

1. **Clone and set up environment**
   ```bash
   python -m venv venv
   source venv/bin/activate   # or venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

2. **Configure MySQL**
   - Create a MySQL 8+ database
   - Run `scraper/schema.sql` to create the tables
   - Copy `.env.example` to `.env` and fill in your credentials

3. **(Optional) Seed dummy data** while waiting for eBay approval
   ```bash
   python scraper/seed_dummy.py
   ```

4. **Run the dashboard**
   ```bash
   streamlit run dashboard/app.py
   ```

5. **Run a one-off fetch** (requires eBay API credentials)
   ```bash
   python scraper/fetcher.py
   ```

---

## Environment Variables

Copy `.env.example` to `.env`:

| Variable | Description |
|---|---|
| `MYSQL_HOST` | MySQL host (e.g., `127.0.0.1` or cloud endpoint) |
| `MYSQL_PORT` | MySQL port (default `3306`) |
| `MYSQL_USER` | MySQL user |
| `MYSQL_PASSWORD` | MySQL password |
| `MYSQL_DATABASE` | Database name (`price_monitor`) |
| `EBAY_CLIENT_ID` | eBay API client ID |
| `EBAY_CLIENT_SECRET` | eBay API client secret |
| `EBAY_ENVIRONMENT` | `SANDBOX` for testing, `PRODUCTION` for live data |

All credentials stay in environment variables — **never hardcoded**.

---

## Design Credits

Visual identity built from scratch to avoid the "Streamlit default" / "AI-made generic" look:
- Palette: charcoal `#1a1d23` base, signal-lime `#ccff00` accent
- Typography: Bebas Neue (display), Inter (body), JetBrains Mono (data)
- Signature element: animated price-drop ticker + tread-pattern background

---

## Roadmap (Future Project Levels)

This is **Level 1 (Easy)** in a progressive portfolio build. Future levels add:

| Level | Feature |
|---|---|
| 2 (Medium) | Multi-marketplace (AliExpress scraping), email/Slack price-drop alerts |
| 3 (Hard) | ML price prediction, proxy rotation, anti-bot stealth |
