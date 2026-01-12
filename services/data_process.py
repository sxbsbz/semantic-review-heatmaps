import pandas as pd

# =============================
# CONFIG
# =============================

INPUT_CSV = "db_restaurant_reviews_strasbourg.csv"
DEDUP_CSV = "db_restaurant_reviews_dedup.csv"
AGGREGATED_CSV = "db_restaurants_aggregated.csv"

# =============================
# LOAD RAW DATA
# =============================

df = pd.read_csv(INPUT_CSV)

print(f"Raw rows: {len(df)}")

# =============================
# STEP 1 — REMOVE DUPLICATE REVIEWS
# =============================

# Drop rows with missing essential data
df = df.dropna(subset=["place_id", "review_text"])

# Remove duplicate reviews per place
df_dedup = df.drop_duplicates(
    subset=["place_id", "review_text"]
)

print(f"After deduplication: {len(df_dedup)} rows")

# Save deduplicated reviews
df_dedup.to_csv(
    DEDUP_CSV,
    index=False,
    encoding="utf-8"
)

# =============================
# STEP 2 — AGGREGATE REVIEWS PER PLACE
# =============================

def aggregate_reviews(series):
    """
    Join all reviews into a single text block.
    Separator chosen to preserve sentence boundaries.
    """
    return "\n\n".join(series)

df_agg = (
    df_dedup
    .groupby("place_id", as_index=False)
    .agg({
        "place_name": "first",
        "latitude": "first",
        "longitude": "first",
        "google_maps_uri": "first",
        "reviews_uri": "first",
        "review_text": aggregate_reviews,
    })
)

# Add review count (very important for weighting later)
df_agg["review_count"] = (
    df_dedup
    .groupby("place_id")["review_text"]
    .count()
    .values
)

print(f"Unique restaurants: {len(df_agg)}")

# Save aggregated dataset
df_agg.to_csv(
    AGGREGATED_CSV,
    index=False,
    encoding="utf-8"
)

print("Processing completed successfully.")
