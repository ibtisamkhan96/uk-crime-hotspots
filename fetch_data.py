"""Fetch street-level crime data from the police.uk open API.

12 months x 8 city centres, 1-mile radius around each centre point.
Rate-limited politely; Greater Manchester is excluded because GMP has
not supplied data to police.uk since 2019.
"""
import json
import time
import urllib.request

import pandas as pd

CITIES = {
    "London (Westminster)": (51.5074, -0.1278),
    "Birmingham": (52.4794, -1.9026),
    "Leeds": (53.7997, -1.5492),
    "Liverpool": (53.4084, -2.9916),
    "Newcastle": (54.9783, -1.6178),
    "Sheffield": (53.3811, -1.4701),
    "Bristol": (51.4545, -2.5879),
    "Nottingham": (52.9548, -1.1581),
}
MONTHS = pd.date_range("2025-05-01", "2026-04-01", freq="MS").strftime("%Y-%m")

rows = []
for city, (lat, lng) in CITIES.items():
    for m in MONTHS:
        url = (f"https://data.police.uk/api/crimes-street/all-crime"
               f"?lat={lat}&lng={lng}&date={m}")
        for attempt in range(4):
            try:
                data = json.load(urllib.request.urlopen(url, timeout=60))
                break
            except Exception as e:
                print(f"  retry {city} {m}: {e}")
                time.sleep(5 * (attempt + 1))
        else:
            data = []
        for c in data:
            rows.append({
                "city": city, "month": m, "category": c["category"],
                "lat": float(c["location"]["latitude"]),
                "lng": float(c["location"]["longitude"]),
                "street": c["location"]["street"]["name"],
            })
        print(city, m, len(data))
        time.sleep(0.8)

df = pd.DataFrame(rows)
df.to_csv("data/street_crimes.csv", index=False)
print("\nTotal:", len(df))
print(df.groupby("city").size())
