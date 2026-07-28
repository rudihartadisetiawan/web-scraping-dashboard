# Case Study: Sneaker Reseller Pricing Intelligence

*Written from the perspective of a client — a dropshipper tracking 50+ sneaker SKUs daily.*

---

## The Problem

I run a dropshipping operation across a few platforms — mostly eBay. I list sneakers from multiple suppliers. Every morning I manually check prices on 5-10 competitor listings to make sure I'm not undercut to death or leaving money on the table.

The problem compounds fast: a supplier changes their price and I don't catch it for three days — I'm either losing margins or losing sales. A competitor runs a flash sale on Air Max 90s and I'm still listing at full price. By the time I notice, the opportunity is gone.

I needed a way to **track prices automatically** across dozens of products, **see the trend over time** (not just today's snapshot), and **get alerted when something drops enough** to be worth re-sourcing.

---

## The Solution

**Sneaker Price Monitor** — a lightweight automated pipeline that:

1. **Fetches eBay pricing data daily** via the official Browse API. No scraping, no blocked IPs, 100% within eBay's terms of service.

2. **Stores every price snapshot** — never overwrites. So I can look back at last Tuesday and see exactly what the Jordan Air 1 Low was selling for.

3. **Surfaces the data in a dashboard** I can check in 30 seconds:

   - Top of the page: how many products I'm tracking, average price, active deals.
   - A **price-drop ticker** that scrolls the biggest movers — hard to miss even at a glance.
   - A line chart where I can pick any sneaker and see its price line for the last 30 days.
   - A **"Top Deals" table** that highlights anything that dropped more than X% (I set the threshold — usually 10%).
   - A **value-for-money ranking** that divides price by seller rating, so I can spot underpriced inventory from high-rated sellers.

---

## What Changed for My Business

| Before | After |
|---|---|
| Manual price checks, 8-10 listings, maybe twice a week | Automated daily tracking across 25+ products (scales to hundreds) |
| "Gut feeling" about price direction | Hard data — 7-day trend lines, day-over-day deltas |
| Caught supplier price changes days late | Daily refresh means I see moves within 24 hours |
| No systematic way to find underpriced inventory | Value-for-money ranking flags exactly that |

**Concrete example:** The dashboard flagged Nike Air Max 90 dropping 24% below its 7-day average. I sourced from a different supplier at the lower price, adjusted my listing, and the margin improvement covered the cost of 2 months of inventory. That one catch alone justified the entire build.

---

## Why This Architecture (Technical Trust Signals)

If you're evaluating this as a template for your own project, here's what matters:

- **API-first, not scraping-first.** eBay's Browse API returns clean JSON with no risk of IP bans, CAPTCHA walls, or breaking selectors. The pipeline runs for months without maintenance.
- **Database designed for time-series.** Every price fetch is an append (new row with a UUID batch tag), never an overwrite. You can audit what price was seen on any given day.
- **Two separate environments, one cloud DB.** The fetcher runs on GitHub Actions (free tier). The dashboard runs on Streamlit Cloud (free tier). Both connect to the same MySQL instance — no syncing files, no data drift.
- **Connection pooling from day one.** SQLAlchemy with `pool_pre_ping=True` prevents the stale-connection errors that plague serverless database access.
- **Parameterized SQL everywhere.** Zero SQL injection surface.

---

## What's Next (Built on This Foundation)

The same pipeline can be extended without throwing anything away:

- **Add AliExpress scraping** for multi-marketplace price comparison.
- **Email/Slack alerts** when a tracked product drops below a target buy price.
- **Price prediction** using historical trend data — forecast where a product is heading next week.

Each of these is additive, not a rewrite. The data model and the daily fetch already collect every data point those features would need.

---

*Built as a Level 1 portfolio project. Designed to be a credible reference for freelance data engineering and dashboard work.*
