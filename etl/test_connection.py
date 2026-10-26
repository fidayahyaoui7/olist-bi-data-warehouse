from sqlalchemy import text

from db import get_engine

with get_engine().connect() as conn:
    print(conn.execute(text("SELECT version()")).scalar())
    n = conn.execute(text("SELECT COUNT(*) FROM dw.dim_order_status")).scalar()
    print("dim_order_status rows:", n)
