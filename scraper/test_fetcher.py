"""Manual sanity test for the eBay fetcher.

Usage:
    python scraper/test_fetcher.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# ponytail: allow running the script directly from the scraper folder
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dotenv import load_dotenv

from scraper.fetcher import get_ebay_token, run_fetch, search_ebay_items


def _credentials_configured() -> bool:
    client_id = os.environ.get("EBAY_CLIENT_ID", "")
    client_secret = os.environ.get("EBAY_CLIENT_SECRET", "")
    return bool(client_id and client_secret and "your_" not in client_id and "your_" not in client_secret)


def main() -> int:
    load_dotenv()

    parser = argparse.ArgumentParser(description="Sanity test eBay Browse API fetcher")
    parser.add_argument("--dry-run", action="store_true", help="Do not write to the database")
    args = parser.parse_args()

    print(f"EBAY_ENVIRONMENT={os.environ.get('EBAY_ENVIRONMENT', 'SANDBOX')}")
    print(f"dry_run={args.dry_run}")

    if not _credentials_configured():
        print("[SKIP] eBay credentials are not set or still contain placeholder values.")
        print("       Set EBAY_CLIENT_ID and EBAY_CLIENT_SECRET in .env to run a live test.")
        return 0

    try:
        token = get_ebay_token()
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] Could not obtain eBay token: {exc}")
        return 1

    print(f"[OK]   eBay token obtained (length={len(token)})")

    try:
        result = search_ebay_items(token, "sneakers", 50, 0)
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] Search request failed: {exc}")
        return 1

    total = result.get("total", 0)
    items = result.get("itemSummaries", []) or []
    print(f"[OK]   Search returned total={total}, items_on_page={len(items)}")

    if args.dry_run:
        print("[INFO] Dry-run: no database writes performed.")
        return 0

    print("[INFO] Live mode: fetching and persisting to MySQL...")
    try:
        run_fetch(dry_run=False)
    except Exception as exc:  # noqa: BLE001
        print(f"[FAIL] Fetch pipeline failed: {exc}")
        return 1

    print("[OK] Live fetch complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
