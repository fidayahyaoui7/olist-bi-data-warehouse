from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db import get_engine

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

DATE_COLS = ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
             "order_delivered_customer_date", "order_estimated_delivery_date"]


def read_keys(conn):
    q = lambda sql: pd.read_sql(text(sql), conn)
    return {
        "customer": q("SELECT customer_key, customer_unique_id FROM dw.dim_customer"),
        "status": q("SELECT order_status_key, order_status FROM dw.dim_order_status"),
        "dates": q("SELECT date_key FROM dw.dim_date"),
    }


def date_key(s):
    # 2017-11-24 -> 20171124 ; missing date -> -1 (rule #5)
    return s.dt.strftime("%Y%m%d").fillna("-1").astype(int)


def build_fact_orders(keys):
    orders = pd.read_csv(RAW / "olist_orders_dataset.csv", parse_dates=DATE_COLS)
    customers = pd.read_csv(RAW / "olist_customers_dataset.csv",
                            usecols=["customer_id", "customer_unique_id"])
    items = pd.read_csv(RAW / "olist_order_items_dataset.csv",
                        usecols=["order_id", "order_item_id", "price", "freight_value"])
    payments = pd.read_csv(RAW / "olist_order_payments_dataset.csv")
    reviews = pd.read_csv(RAW / "olist_order_reviews_dataset.csv",
                          usecols=["order_id", "review_score", "review_answer_timestamp"],
                          parse_dates=["review_answer_timestamp"])

    # Keys of the shared dimensions
    f = orders.merge(customers, on="customer_id", how="left")
    f = f.merge(keys["customer"], on="customer_unique_id", how="left")
    f = f.merge(keys["status"], on="order_status", how="left")

    # Items aggregated per order
    it = (items.assign(total=items.price + items.freight_value)
               .groupby("order_id")
               .agg(items_count=("order_item_id", "size"), items_total=("total", "sum"))
               .reset_index())

    # Rule #18: payments aggregated per order BEFORE joining
    pay = (payments.groupby("order_id")
                   .agg(payment_total=("payment_value", "sum"),
                        payment_count=("payment_sequential", "count"),
                        max_installments=("payment_installments", "max"))
                   .reset_index())
    main_type = (payments.sort_values(["order_id", "payment_value", "payment_sequential"],
                                      ascending=[True, False, True])
                         .drop_duplicates("order_id")[["order_id", "payment_type"]]
                         .rename(columns={"payment_type": "main_payment_type"}))

    # Rule #19: keep only the LATEST review of each order
    rev = (reviews.sort_values("review_answer_timestamp", ascending=False)
                  .drop_duplicates("order_id")[["order_id", "review_score"]])

    for part in (it, pay, main_type, rev):
        f = f.merge(part, on="order_id", how="left")

    # Rules #16/#21: orders without items or payments keep a count of 0
    f["items_count"] = f.items_count.fillna(0).astype(int)
    f["payment_count"] = f.payment_count.fillna(0).astype(int)

    # Rules #3/#4: delivery metrics only for delivered orders WITH a delivery date
    delivered = (f.order_status == "delivered") & f.order_delivered_customer_date.notna()
    d_deliv = f.order_delivered_customer_date.dt.normalize()
    d_est = f.order_estimated_delivery_date.dt.normalize()
    d_purch = f.order_purchase_timestamp.dt.normalize()

    f["delivery_days"] = (d_deliv - d_purch).dt.days.where(delivered)
    f["delay_days"] = (d_deliv - d_est).dt.days.where(delivered)   # negative = early
    f["is_on_time"] = pd.Series(pd.NA, index=f.index, dtype="boolean")
    f.loc[delivered, "is_on_time"] = f.loc[delivered, "delay_days"] <= 0

    # Rule #5: date keys, -1 when the date is missing
    f["purchase_date_key"] = date_key(f.order_purchase_timestamp)
    f["approved_date_key"] = date_key(f.order_approved_at)
    f["carrier_date_key"] = date_key(f.order_delivered_carrier_date)
    f["delivered_date_key"] = date_key(f.order_delivered_customer_date)
    f["estimated_date_key"] = date_key(f.order_estimated_delivery_date)

    for c in ["delivery_days", "delay_days", "max_installments", "review_score"]:
        f[c] = f[c].astype("Int64")

    cols = ["order_id", "customer_key", "order_status_key", "purchase_date_key",
            "approved_date_key", "carrier_date_key", "delivered_date_key",
            "estimated_date_key", "delivery_days", "delay_days", "is_on_time",
            "items_count", "items_total", "payment_total", "payment_count",
            "max_installments", "main_payment_type", "review_score"]
    return f[cols], int(delivered.sum())


def main():
    engine = get_engine()
    with engine.connect() as conn:
        keys = read_keys(conn)

    df, n_delivered = build_fact_orders(keys)

    # Safety checks BEFORE writing anything
    assert df.order_id.is_unique, "order_id must be unique"
    assert df[["customer_key", "order_status_key"]].notna().all().all(), "missing keys"
    valid = set(keys["dates"].date_key)
    for c in [c for c in df.columns if c.endswith("_date_key")]:
        assert df[c].isin(valid).all(), f"{c} has dates missing from dim_date"

    both = df.dropna(subset=["items_total", "payment_total"])
    mismatch = ((both.payment_total - both.items_total).round(2).abs() > 0.01).sum()
    print("Rows to load:", len(df))
    print("Orders without items:", (df.items_count == 0).sum())
    print("Orders with delivery metrics:", n_delivered)
    print("Payment vs items mismatch (rule #20):", mismatch, "of", len(both))

    with engine.begin() as conn:
        conn.execute(text("DELETE FROM dw.fact_orders"))
        df.to_sql("fact_orders", conn, schema="dw", if_exists="append",
                  index=False, method="multi", chunksize=5000)
        rows = conn.execute(text("SELECT COUNT(*) FROM dw.fact_orders")).scalar()
        assert rows == len(df), "row count mismatch"   # rollback if it fails
    print("fact_orders loaded:", rows, "rows")


if __name__ == "__main__":
    main()
