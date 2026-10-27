from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db import get_engine

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"


def read_keys(conn):
    """Read the surrogate keys from the dimensions already loaded."""
    q = lambda sql: pd.read_sql(text(sql), conn)
    return {
        "customer": q("SELECT customer_key, customer_unique_id FROM dw.dim_customer"),
        "product": q("SELECT product_key, product_id FROM dw.dim_product"),
        "seller": q("SELECT seller_key, seller_id FROM dw.dim_seller"),
        "status": q("SELECT order_status_key, order_status FROM dw.dim_order_status"),
        "dates": q("SELECT date_key FROM dw.dim_date"),
    }


def build_fact_sales(keys):
    items = pd.read_csv(
        RAW / "olist_order_items_dataset.csv",
        usecols=["order_id", "order_item_id", "product_id", "seller_id", "price", "freight_value"],
    )
    orders = pd.read_csv(
        RAW / "olist_orders_dataset.csv",
        usecols=["order_id", "customer_id", "order_status", "order_purchase_timestamp"],
        parse_dates=["order_purchase_timestamp"],
    )
    customers = pd.read_csv(
        RAW / "olist_customers_dataset.csv", usecols=["customer_id", "customer_unique_id"]
    )

    # customer_id (per order) -> customer_unique_id (real person) -> customer_key
    f = items.merge(orders, on="order_id", how="left")
    f = f.merge(customers, on="customer_id", how="left")
    f = f.merge(keys["customer"], on="customer_unique_id", how="left")
    f = f.merge(keys["product"], on="product_id", how="left")
    f = f.merge(keys["seller"], on="seller_id", how="left")
    f = f.merge(keys["status"], on="order_status", how="left")

    # Strict check: every item must find all its keys
    key_cols = ["customer_key", "product_key", "seller_key", "order_status_key",
                "order_purchase_timestamp"]
    missing = f[key_cols].isna().sum()
    assert missing.sum() == 0, f"Missing keys:\n{missing}"

    f["purchase_date_key"] = f.order_purchase_timestamp.dt.strftime("%Y%m%d").astype(int)

    return f[["order_id", "order_item_id", "purchase_date_key", "customer_key",
              "product_key", "seller_key", "order_status_key", "price", "freight_value"]]


def main():
    engine = get_engine()

    with engine.connect() as conn:
        keys = read_keys(conn)

    df = build_fact_sales(keys)

    # Safety checks BEFORE writing anything
    assert not df.duplicated(["order_id", "order_item_id"]).any(), "duplicate items"
    assert df.purchase_date_key.isin(set(keys["dates"].date_key)).all(), "date not in dim_date"
    print("Rows to load:", len(df))

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM dw.fact_sales"))
        df.to_sql("fact_sales", conn, schema="dw", if_exists="append",
                  index=False, method="multi", chunksize=5000)

        rows, price, freight = conn.execute(text(
            "SELECT COUNT(*), SUM(price), SUM(freight_value) FROM dw.fact_sales"
        )).one()

        # Reconciliation: if a total does not match, the transaction is rolled back
        assert rows == len(df), "row count mismatch"
        assert abs(float(price) - df.price.sum()) < 0.01, "price total mismatch"
        assert abs(float(freight) - df.freight_value.sum()) < 0.01, "freight total mismatch"

    print(f"fact_sales loaded: {rows} rows | price {float(price):,.2f} | freight {float(freight):,.2f}")


if __name__ == "__main__":
    main()
