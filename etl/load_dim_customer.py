from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db import get_engine

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def build_dim_customer():
    customers = pd.read_csv(RAW / "olist_customers_dataset.csv")
    orders = pd.read_csv(
        RAW / "olist_orders_dataset.csv",
        usecols=["customer_id", "order_purchase_timestamp"],
        parse_dates=["order_purchase_timestamp"],
    )
    geo = pd.read_csv(RAW / "olist_geolocation_dataset.csv")

    # Rules #1 and #23: the real customer is customer_unique_id.
    # We keep the address of the LATEST order (SCD Type 1).
    c = customers.merge(orders, on="customer_id", how="left")
    c = c.sort_values("order_purchase_timestamp", ascending=False)
    c = c.drop_duplicates(subset="customer_unique_id", keep="first")

    # Rule #2: geolocation has duplicates -> remove them, then
    # keep ONE row per zip prefix with the average coordinates.
    geo = geo.drop_duplicates()
    geo_zip = (
        geo.groupby("geolocation_zip_code_prefix")[["geolocation_lat", "geolocation_lng"]]
        .mean()
        .reset_index()
    )

    # Rule #22: LEFT join, customers with an unknown zip keep NULL coordinates.
    c = c.merge(
        geo_zip,
        left_on="customer_zip_code_prefix",
        right_on="geolocation_zip_code_prefix",
        how="left",
    )

    out = c.rename(
        columns={
            "customer_zip_code_prefix": "zip_code_prefix",
            "customer_city": "city",
            "customer_state": "state",
            "geolocation_lat": "latitude",
            "geolocation_lng": "longitude",
        }
    )[["customer_unique_id", "zip_code_prefix", "city", "state", "latitude", "longitude"]]

    return out


def main():
    df = build_dim_customer()

    # Safety checks BEFORE writing anything
    assert df.customer_unique_id.is_unique, "customer_unique_id must be unique"
    print("Rows to load:", len(df))
    print("Rows without coordinates:", df.latitude.isna().sum())

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM dw.dim_customer"))
        df.to_sql("dim_customer", conn, schema="dw", if_exists="append",
                  index=False, method="multi", chunksize=5000)
        total = conn.execute(text("SELECT COUNT(*) FROM dw.dim_customer")).scalar()
    print("dim_customer loaded:", total, "rows")


if __name__ == "__main__":
    main()
