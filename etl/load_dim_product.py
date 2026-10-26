from pathlib import Path

import pandas as pd
from sqlalchemy import text

from db import get_engine

RAW = Path(__file__).resolve().parent.parent / "data" / "raw"

# Rule #15: categories missing from the translation file.
# The second English name is my own reading of the Portuguese, review it.
MANUAL_TRANSLATION = {
    "pc_gamer": "pc_gamer",
    "portateis_cozinha_e_preparadores_de_alimentos": "portable_kitchen_and_food_preparers",
}


def build_dim_product():
    products = pd.read_csv(RAW / "olist_products_dataset.csv")
    trans = pd.read_csv(RAW / "product_category_name_translation.csv")

    # Rule #13: fix the misspelled column names and use clean names
    products = products.rename(columns={
        "product_category_name": "category_name_pt",
        "product_name_lenght": "name_length",
        "product_description_lenght": "description_length",
        "product_photos_qty": "photos_qty",
        "product_weight_g": "weight_g",
        "product_length_cm": "length_cm",
        "product_height_cm": "height_cm",
        "product_width_cm": "width_cm",
    })
    trans = trans.rename(columns={
        "product_category_name": "category_name_pt",
        "product_category_name_english": "category_name_en",
    })

    # Rule #8: English names through the translation file (LEFT join)
    p = products.merge(trans, on="category_name_pt", how="left")

    # Rule #15: manual mapping for the 2 missing translations
    manual = p.category_name_pt.map(MANUAL_TRANSLATION)
    p["category_name_en"] = p.category_name_en.fillna(manual)

    # Rule #7: products without any category become 'unknown'
    p["category_name_pt"] = p.category_name_pt.fillna("unknown")
    p["category_name_en"] = p.category_name_en.fillna("unknown")

    # Integer columns contain NaN, so use pandas nullable integers
    int_cols = ["name_length", "description_length", "photos_qty",
                "weight_g", "length_cm", "height_cm", "width_cm"]
    p[int_cols] = p[int_cols].astype("Int64")

    return p[["product_id", "category_name_pt", "category_name_en"] + int_cols]


def main():
    df = build_dim_product()

    # Safety checks BEFORE writing anything
    assert df.product_id.is_unique, "product_id must be unique"
    unknown = (df.category_name_pt == "unknown").sum()
    untranslated = ((df.category_name_en == "unknown") & (df.category_name_pt != "unknown")).sum()
    print("Rows to load:", len(df))
    print("Products with unknown category:", unknown)
    print("Categories still untranslated (must be 0):", untranslated)

    engine = get_engine()
    with engine.begin() as conn:
        conn.execute(text("DELETE FROM dw.dim_product"))
        df.to_sql("dim_product", conn, schema="dw", if_exists="append",
                  index=False, method="multi", chunksize=5000)
        total = conn.execute(text("SELECT COUNT(*) FROM dw.dim_product")).scalar()
    print("dim_product loaded:", total, "rows")


if __name__ == "__main__":
    main()
