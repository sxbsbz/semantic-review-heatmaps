import time
import math
import pandas as pd
import csv
from google_apis import create_service

# =============================
# CONFIGURATION
# =============================

OUTPUT_CSV = "db_restaurant_reviews_strasbourg.csv"

MAX_API_CALLS = 800          # hard stop
SLEEP_SECONDS = 0.2          # safety sleep
SEARCH_RADIUS_METERS = 600   # same as before
GRID_STEP_METERS = 450       # overlap to avoid gaps

LANGUAGE_CODE = "fr"
REGION_CODE = "FR"

# Approximate bounding box for Strasbourg
# (rectangle version, as requested)
LAT_MIN = 48.530
LAT_MAX = 48.640
LON_MIN = 7.67
LON_MAX = 7.83

# =============================
# GOOGLE PLACES SERVICE
# =============================

client_secret_file = "client_secret.json"
API_NAME = "places"
API_VERSION = "v1"
SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]

service = create_service(
    client_secret_file,
    API_NAME,
    API_VERSION,
    SCOPES
)

# =============================
# GRID UTILITIES
# =============================

def meters_to_lat(meters):
    return meters / 111_320

def meters_to_lon(meters, latitude):
    return meters / (111_320 * math.cos(math.radians(latitude)))

def generate_grid(lat_min, lat_max, lon_min, lon_max, step_meters):
    points = []
    lat = lat_min
    while lat <= lat_max:
        lon = lon_min
        lon_step = meters_to_lon(step_meters, lat)
        while lon <= lon_max:
            points.append((lat, lon))
            lon += lon_step
        lat += meters_to_lat(step_meters)
    return points

# =============================
# CSV INITIALIZATION
# =============================

columns = [
    "place_id",
    "place_name",
    "latitude",
    "longitude",
    "review_text",
    "google_maps_uri",
    "reviews_uri"
]

# Create CSV with header if it does not exist
try:
    pd.read_csv(OUTPUT_CSV)
except FileNotFoundError:
    pd.DataFrame(columns=columns).to_csv(
        OUTPUT_CSV,
        index=False,
        quoting=csv.QUOTE_ALL,
        encoding="utf-8"
    )

# =============================
# MAIN SCRAPER
# =============================

grid_points = generate_grid(
    LAT_MIN, LAT_MAX,
    LON_MIN, LON_MAX,
    GRID_STEP_METERS
)

api_calls = 0
rows_buffer = []

for lat, lon in grid_points:

    if api_calls >= MAX_API_CALLS:
        print("Reached API call limit.")
        break

    request_body = {
        "languageCode": LANGUAGE_CODE,
        "regionCode": REGION_CODE,
        "includedPrimaryTypes": "restaurant",
        "maxResultCount": 20,
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": lat,
                    "longitude": lon
                },
                "radius": SEARCH_RADIUS_METERS
            }
        },
        "rankPreference": "DISTANCE"
    }

    response = service.places().searchNearby(
        body=request_body,
        fields=(
            "places(id,"
            "displayName,"
            "location,"
            "reviews,"
            "googleMapsLinks)"
        )
    ).execute()

    api_calls += 1
    print(f"API call {api_calls} at ({lat:.5f}, {lon:.5f})")

    for place in response.get("places", []):

        place_id = place.get("id")
        place_name = place.get("displayName", {}).get("text")
        location = place.get("location", {})
        latitude = location.get("latitude")
        longitude = location.get("longitude")

        maps_links = place.get("googleMapsLinks", {})
        google_maps_uri = maps_links.get("placeUri")
        reviews_uri = maps_links.get("reviewsUri")

        reviews = place.get("reviews", [])

        # One row per review
        for review in reviews:
            review_text = review.get("text", {}).get("text")

            rows_buffer.append({
                "place_id": place_id,
                "place_name": place_name,
                "latitude": latitude,
                "longitude": longitude,
                "review_text": review_text,
                "google_maps_uri": google_maps_uri,
                "reviews_uri": reviews_uri
            })

    # Flush buffer periodically (important for large runs)
    if len(rows_buffer) >= 500:
        pd.DataFrame(rows_buffer).to_csv(
            OUTPUT_CSV,
            mode="a",
            header=False,
            index=False,
            quoting=csv.QUOTE_ALL,
            encoding="utf-8"
        )
        rows_buffer.clear()

    time.sleep(SLEEP_SECONDS)

# Final flush
if rows_buffer:
    pd.DataFrame(rows_buffer).to_csv(
        OUTPUT_CSV,
        mode="a",
        header=False,
        index=False,
        quoting=csv.QUOTE_ALL,
        encoding="utf-8"
    )

print("Scraping completed.")
