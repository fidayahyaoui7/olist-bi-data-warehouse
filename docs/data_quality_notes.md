# Data Quality Notes

Findings from `notebooks/01_data_profiling.ipynb`. Each issue maps to a rule applied later in the ETL (Step 3). Raw files are never modified.

## 1. Dataset overview

| Table | Rows | Grain |
|---|---|---|
| customers | 99,441 | one customer_id (one per order) |
| geolocation | 1,000,163 | one coordinate point (many per zip prefix) |
| order_items | 112,650 | one item within an order |
| order_payments | 103,886 | one payment of an order |
| order_reviews | 99,224 | one review |
| orders | 99,441 | one order |
| products | 32,951 | one product |
| sellers | 3,095 | one seller |
| category_translation | 71 | one category |

Period covered: 2016-09-04 to 2018-10-17.

## 2. Issues and handling rules

| # | Issue | Evidence | Impact | Handling rule |
|---|---|---|---|---|
| 1 | customer_id is generated per order | 99,441 customer_id vs 96,096 customer_unique_id | Repeat purchase rate would show 0% | Customer dimension uses customer_unique_id |
| 2 | Duplicate rows in geolocation | 261,831 duplicated rows (26%) | Inflated dimension, bad joins | Deduplicate, keep one row per zip prefix (average lat/long) |
| 3 | Delivered orders without delivery date | 8 orders with status delivered and null delivered_customer_date | Delivery KPIs would fail or be biased | Delivery KPIs use status delivered AND non-null delivery date (96,470 orders) |
| 4 | Canceled orders with a delivery date | 6 canceled orders have a delivery date | Inconsistent status | Keep as canceled, exclude from revenue and delivery KPIs |
| 5 | Null dates on orders not yet delivered | 2,965 null delivered_customer_date, all explained by status except issue 3 | None if handled | Keep NULL, never fill |
| 6 | Orders not completed | 625 canceled, 609 unavailable, 1,729 in progress | Revenue overstated | Revenue excludes canceled and unavailable |
| 7 | Missing product category | 610 products (1.85%) | Unclassified sales | Label as "unknown" |
| 8 | Categories in Portuguese | translation table has 71 rows | Unreadable reports | Join with translation table, check for missing translations |
| 9 | Sparse months at the edges | 2016-09 to 2016-12 (4, 324, 0, 1 orders), 2018-09 (16), 2018-10 (4) | Distorted trend charts | Keep in warehouse, dashboards focus on 2017-01 to 2018-08 |
| 10 | Missing month in orders | No orders in 2016-11 | Date gaps in charts | Date dimension is a full generated calendar |
| 11 | Several payments and items per order | payments 103,886 and items 112,650 vs 99,441 orders | Duplicated amounts when joining | Aggregate payments per order before joining, sales fact at item grain |
| 12 | Optional review text | 88% null titles, 59% null messages | None | Keep, analysis relies on review_score |
| 13 | Misspelled column names | product_name_lenght, product_description_lenght | Confusion | Rename in the product dimension |
| 14 | Outlier customer | one customer_unique_id with 17 orders | Skews customer analysis | Flag, review in customer analysis |

## 3. Verified findings

- 97.0% of orders are delivered, cancellation rate is 0.63% (625 / 99,441).
- Repeat purchase rate is 3.12% (2,997 of 96,096 customers, all statuses). 96.9% of customers bought once. To be recomputed in the warehouse with the exclusion rules.
- Orders grew 135% between Jan-Aug 2017 (22,968) and Jan-Aug 2018 (53,991), then plateaued from March 2018.
- Black Friday (Nov 2017) is the peak month with 7,544 orders.


## 4. Join and relationship checks

| # | Check | Result | Handling rule |
|---|---|---|---|
| 15 | Categories without translation | 2 (pc_gamer, portateis_cozinha_e_preparadores_de_alimentos) | Add manual mapping in the product dimension |
| 16 | Orders without any item | 775: 603 unavailable, 164 canceled, 5 created, 2 invoiced, 1 shipped, 0 delivered | These orders are absent from the sales fact (item grain). Revenue filters on status because 461 canceled orders do have items. Cancellation rate is computed on the orders table |
| 17 | Items with unknown product | 0 | Plain join items to products is safe |
| 18 | Orders with 2+ payments | 2,961 (3.0%) | Aggregate payments per order before joining |
| 19 | Orders with 2+ reviews | 547 | Keep the latest review per order (review_answer_timestamp) |

## 5. Still to verify

- Whether payment totals match item price + freight per order.
- Zip prefixes in customers and sellers that are missing from geolocation.
