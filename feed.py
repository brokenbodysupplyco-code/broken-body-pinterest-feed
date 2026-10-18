"""Generate a Pinterest catalog CSV from Fourthwall published product offers.

Uses Fourthwall Open API Basic credentials stored as GitHub Actions secrets.
The endpoint may differ in authentication from other Fourthwall APIs; failures
are explicit and never overwrite the last good catalog.
"""
import csv
import html
import os
import re
import sys
from pathlib import Path
from urllib.parse import urlparse, quote

import requests
from requests.auth import HTTPBasicAuth

API_URL = "https://storefront.fourthwall.com/api/product-offers"
STORE_URL = os.getenv("FOURTHWALL_STORE_URL", "https://brokenbodysupplyco.com").rstrip("/")
OUTPUT = Path("docs/products.csv")
FIELDS = ["id", "title", "description", "link", "image_link", "price", "availability", "condition"]


def clean(value):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]*>", " ", str(value or "")))).strip()


def url_value(value):
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, dict):
        for key in ("url", "src", "originalUrl", "imageUrl"):
            if isinstance(value.get(key), str):
                return value[key].strip()
    return ""


def image_url(offer):
    for key in ("primaryImageUrl", "imageUrl", "image_link"):
        result = url_value(offer.get(key))
        if result:
            return result
    images = offer.get("images") or offer.get("imageUrls") or []
    for image in images:
        result = url_value(image)
        if result:
            return result
    return ""


def offer_link(offer):
    for key in ("url", "productUrl", "product_url", "storefrontUrl", "link"):
        candidate = url_value(offer.get(key))
        if candidate.startswith("https://"):
            return candidate
        if candidate.startswith("/products/"):
            return STORE_URL + candidate
    slug = offer.get("slug")
    if isinstance(slug, str) and slug.strip():
        # Standard Fourthwall product path. Verify a sample URL before submitting to Pinterest.
        return STORE_URL + "/products/" + quote(slug.strip(), safe="-")
    return ""


def price_value(offer):
    price = offer.get("price")
    if isinstance(price, dict):
        amount = price.get("amount")
        currency = price.get("currency", "USD")
        if amount is not None:
            return f"{int(amount) / 100:.2f} {currency}"
    # Only use explicit variant prices when API's offer-level price is absent.
    variants = offer.get("variants") or []
    candidates = []
    for variant in variants:
        if not isinstance(variant, dict):
            continue
        p = variant.get("price")
        if isinstance(p, dict) and p.get("amount") is not None:
            candidates.append((int(p["amount"]) / 100, p.get("currency", "USD")))
    if candidates:
        amount, currency = min(candidates)
        return f"{amount:.2f} {currency}"
    return ""


def fetch_offers():
    user = os.getenv("FOURTHWALL_API_USER")
    password = os.getenv("FOURTHWALL_API_PASSWORD")
    if not user or not password:
        raise RuntimeError("Missing FOURTHWALL_API_USER or FOURTHWALL_API_PASSWORD GitHub secret")
    session = requests.Session()
    session.auth = HTTPBasicAuth(user, password)
    session.headers.update({"Accept": "application/json"})
    page, limit = 0, 50
    while True:
        response = session.get(API_URL, params={"page": page, "limit": limit}, timeout=45)
        if response.status_code in (401, 403):
            raise RuntimeError(f"Fourthwall rejected Basic authentication (HTTP {response.status_code}). The Product Offer endpoint may require a Bearer token. No feed was published.")
        response.raise_for_status()
        payload = response.json()
        results = payload.get("results")
        if not isinstance(results, list):
            raise RuntimeError("Unexpected API response: missing 'results' list")
        yield from results
        page += 1
        total = payload.get("totalCount")
        if not results or (total is not None and page * limit >= int(total)):
            break
        if page > 1000:
            raise RuntimeError("Unexpected pagination length; stopping")


def main():
    rows, skipped = [], 0
    for offer in fetch_offers():
        if not isinstance(offer, dict):
            skipped += 1
            continue
        link, picture, price = offer_link(offer), image_url(offer), price_value(offer)
        if not (offer.get("id") and offer.get("name") and link and picture and price):
            skipped += 1
            continue
        if urlparse(link).scheme != "https" or urlparse(picture).scheme != "https":
            skipped += 1
            continue
        rows.append({
            "id": str(offer["id"]),
            "title": clean(offer["name"])[:150],
            "description": clean(offer.get("description"))[:5000] or clean(offer["name"]),
            "link": link,
            "image_link": picture,
            "price": price,
            "availability": "in stock",
            "condition": "new",
        })
    if not rows:
        raise RuntimeError(f"No valid products ({skipped} skipped). Not replacing any existing feed. Check API response field names.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    temporary = OUTPUT.with_suffix(".csv.tmp")
    with temporary.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(OUTPUT)
    print(f"Created {OUTPUT}: {len(rows)} offers; {skipped} skipped. Validate URLs and prices before submitting to Pinterest.")


if __name__ == "__main__":
    try:
        main()
    except (requests.RequestException, ValueError, RuntimeError) as error:
        print(f"FEED FAILED: {error}", file=sys.stderr)
        sys.exit(1)
