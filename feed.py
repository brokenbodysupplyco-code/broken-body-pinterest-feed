"""Generate a Pinterest-compatible product feed from Fourthwall's Product Offer API.

Credentials are read only from environment variables. Never commit API keys.
"""
import csv
import html
import os
import re
from pathlib import Path

import requests

API_URL = "https://storefront.fourthwall.com/api/product-offers"
STORE_URL = os.environ["FOURTHWALL_STORE_URL"].rstrip("/")
API_KEY = os.environ["FOURTHWALL_API_KEY"]
OUTPUT = Path("public/products.csv")


def plain_text(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", value or ""))).strip()


def image_url(offer):
    images = offer.get("images") or []
    if images:
        first = images[0]
        if isinstance(first, str):
            return first
        if isinstance(first, dict):
            return first.get("url") or first.get("src") or ""
    return ""


def offer_link(offer):
    # Confirm the exact product URL shape in the API response before production use.
    return offer.get("url") or offer.get("productUrl") or ""


def fetch_offers():
    session = requests.Session()
    session.headers.update({"Authorization": f"Bearer {API_KEY}"})
    page = 0
    while True:
        response = session.get(API_URL, params={"page": page, "limit": 50}, timeout=40)
        response.raise_for_status()
        data = response.json()
        results = data.get("results") or []
        if not isinstance(results, list):
            raise ValueError("Unexpected Fourthwall API response: results is not a list")
        yield from results
        page += 1
        if not results or page * 50 >= int(data.get("totalCount", 0)):
            break


def main():
    rows = []
    skipped = 0
    for offer in fetch_offers():
        price_obj = offer.get("price") or {}
        amount = price_obj.get("amount")
        currency = price_obj.get("currency") or "USD"
        link = offer_link(offer)
        picture = image_url(offer)
        if not all([offer.get("id"), offer.get("name"), amount is not None, link, picture]):
            skipped += 1
            continue
        rows.append({
            "id": str(offer["id"]),
            "title": plain_text(offer["name"])[:150],
            "description": plain_text(offer.get("description"))[:5000],
            "link": link,
            "image_link": picture,
            "price": f"{int(amount) / 100:.2f} {currency}",
            "availability": "in stock",
            "condition": "new",
        })
    if not rows:
        raise RuntimeError("No complete products found; refusing to publish an empty feed. Check API fields and product URLs.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} products to {OUTPUT}; skipped {skipped} incomplete products")


if __name__ == "__main__":
    main()
