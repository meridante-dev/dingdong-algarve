#!/usr/bin/env python3
"""Century 21 Portugal → Roam & Root feed.
Pulls current Algarve (Faro district, addresses=08) SALE listings from
century21.pt's own public JSON API and writes a lean data/c21-algarve.json
for the catalog page. Run by GitHub Actions daily; safe to run by hand.
"""
import json, ssl, time, urllib.request
from datetime import datetime, timezone

API   = "https://www.century21.pt/api/properties"
QUERY = "addresses=08&ad_type=sell&order_by=entered_market_desc"
PAGES = 8          # 8 × 20 = newest 160 listings
OUT   = "data/c21-algarve.json"
UA    = {"User-Agent": "Mozilla/5.0 (RoamRootAlgarve feed; partner agent site)"}

def get(url):
    req = urllib.request.Request(url, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=30))

def lean(r):
    t = r.get("title") or {}
    return {
        "ref":     r.get("reference"),
        "title":   {k: t.get(k) for k in ("en","pt","fr") if t.get(k)},
        "price":   r.get("price"),
        "hidden":  bool(r.get("price_hidden")),
        "type":    r.get("asset_type"),
        "rooms":   r.get("number_of_rooms"),
        "wcs":     r.get("number_of_wcs"),
        "area":    r.get("gross_area") or r.get("useful_area"),
        "address": r.get("address"),
        "lat":     r.get("lat"), "lng": r.get("lng"),
        "link":    r.get("link"),
        "images":  (r.get("images") or [])[:3],
        "chars":   r.get("characteristics") or [],
        "entered": r.get("entered_market"),
        "agency":  (r.get("agency") or {}).get("name") if isinstance(r.get("agency"), dict) else r.get("agency"),
    }

def main():
    items, total = [], None
    for page in range(1, PAGES + 1):
        d = get(f"{API}?{QUERY}&page={page}")
        total = d.get("total", total)
        batch = d.get("data") or []
        if not batch: break
        items += [lean(r) for r in batch]
        time.sleep(1.2)                     # be polite
    seen, dedup = set(), []
    for it in items:
        if it["ref"] and it["ref"] not in seen:
            seen.add(it["ref"]); dedup.append(it)
    out = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "source": "century21.pt public listings API — Faro district, sales, newest first",
        "total_in_region": total,
        "count": len(dedup),
        "listings": dedup,
    }
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
    print(f"wrote {OUT}: {len(dedup)} listings of {total} in region")

if __name__ == "__main__":
    main()
