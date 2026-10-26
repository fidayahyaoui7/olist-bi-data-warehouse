from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db import get_engine

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def build_dim_seller():
    sellers = pd.read_csv(RAW / "olist_sellers_dataset.csv")
    geo = pd.read_csv(RAW / "olist_geolocation_dataset.csv")

    # Rule #2: remove duplicates, then one row per zip prefix (average coordinates)
    geo = geo.drop_duplicates()
    geo_zip = (
        geo.groupby("geolocation_zip_code_prefix")[["geolocation_lat", "geolocation_lng"]]
        .mean()
        .reset_index()
    )

    # Rule #22: LEFT join, sellers with an unknown zip keep NULL coordinates
    s = sellers.merge(
        geo_zip,
        left_on="seller_zip_code_prefix",
        right_on="geolocation_zip_code_prefix",
        how="left",
    )

    return s.rename(
        columns={
            "seller_zip_code_prefix": "zip_code_prefix",
            "seller_city": "city",
            "seller_state": "state",
            "geolocation_lat": "latitude",
            "geolocation_lng": "longitude",
        }
    )[["seller_id", "zip_code_prefix", "city", "state", "latitude", "longitude"]]


def main():
    df = build_dim_seller()

    # Safety checks BEFORE writing anything
    assert df.seller_id.is_unique, "seller_id must be unique"
    print("Rows to load:", len(df))
    print("Rows without coordinates:", df.latitude.isna().sum())

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM dw.dim_seller"))
        df.to_sql("dim_seller", conn, schema="dw", if_exists="append",
                  index=False, method="multi", chunksize=5000)
        total = conn.execute(text("SELECT COUNT(*) FROM dw.dim_seller")).scalar()
    print("dim_seller loaded:", total, "rows")


if __name__ == "__main__":
    main()
