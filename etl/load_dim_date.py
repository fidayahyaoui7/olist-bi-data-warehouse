import pandas as pd
from sqlalchemy import text

from db import get_engine

START, END = "2016-01-01", "2018-12-31"


def build_dim_date():
    # 1) one row per calendar day
    d = pd.DataFrame({"full_date": pd.date_range(START, END, freq="D")})

    # 2) the key: 2017-11-24 becomes the integer 20171124
    d["date_key"] = d.full_date.dt.strftime("%Y%m%d").astype(int)

    # 3) attributes used to group and filter in the dashboards
    d["year"] = d.full_date.dt.year
    d["quarter"] = d.full_date.dt.quarter
    d["month"] = d.full_date.dt.month
    d["month_name"] = d.full_date.dt.month_name()
    d["year_month"] = d.full_date.dt.strftime("%Y-%m")
    d["week_of_year"] = d.full_date.dt.isocalendar().week.astype(int)
    d["day_of_week"] = d.full_date.dt.dayofweek + 1   # 1 = Monday ... 7 = Sunday
    d["day_name"] = d.full_date.dt.day_name()
    d["is_weekend"] = d.day_of_week >= 6
    d["full_date"] = d.full_date.dt.date

    return d[["date_key", "full_date", "year", "quarter", "month", "month_name",
              "year_month", "week_of_year", "day_of_week", "day_name", "is_weekend"]]


def main():
    df = build_dim_date()
    engine = get_engine()
    with engine.begin() as conn:
        # keep the special row -1 ("Not available"), reload everything else
        conn.execute(text("DELETE FROM dw.dim_date WHERE date_key <> -1"))
        df.to_sql("dim_date", conn, schema="dw", if_exists="append", index=False)
        total = conn.execute(text("SELECT COUNT(*) FROM dw.dim_date")).scalar()
    print(f"dim_date loaded: {len(df)} days + the -1 row = {total} rows")


if __name__ == "__main__":
    main()
