import sys
import time
from pathlib import Path

from sqlalchemy import text

import load_dim_customer
import load_dim_date
import load_dim_product
import load_dim_seller
import load_fact_orders
import load_fact_sales
from db import get_engine

CHECKS_FILE = Path(__file__).resolve().parent.parent / "sql" / "02_quality_checks.sql"

# Order matters: dimensions first, facts after
STEPS = [
    ("dim_date", load_dim_date.main),
    ("dim_customer", load_dim_customer.main),
    ("dim_product", load_dim_product.main),
    ("dim_seller", load_dim_seller.main),
    ("fact_sales", load_fact_sales.main),
    ("fact_orders", load_fact_orders.main),
]


def clear_facts():
    """Facts reference the dimensions (foreign keys), so they are emptied first."""
    with get_engine().begin() as conn:
        conn.execute(text("DELETE FROM dw.fact_sales"))
        conn.execute(text("DELETE FROM dw.fact_orders"))
    print("Fact tables emptied (full refresh)")


def run_checks():
    sql = CHECKS_FILE.read_text(encoding="utf-8")
    with get_engine().connect() as conn:
        rows = conn.exec_driver_sql(sql).fetchall()
    failed = 0
    for name, expected, actual, status in rows:
        print(f"[{status}] {name}: expected {expected}, actual {actual}")
        if status != "PASS":
            failed += 1
    return len(rows), failed


def main():
    start = time.time()
    print("=== ETL run started ===")
    clear_facts()

    for name, step in STEPS:
        print(f"\n--- {name} ---")
        step()

    print("\n--- quality checks ---")
    total, failed = run_checks()

    print(f"\n=== Done in {time.time() - start:.0f}s | {total - failed}/{total} checks passed ===")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
