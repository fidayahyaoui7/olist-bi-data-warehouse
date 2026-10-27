-- Quality checks for the Olist data warehouse.
-- Every row must be PASS. A FAIL means the ETL or the data changed.

WITH checks AS (
    -- Row counts
    SELECT 'dim_date rows' AS check_name, 1097::bigint AS expected,
           (SELECT COUNT(*) FROM dw.dim_date) AS actual
    UNION ALL SELECT 'dim_customer rows (one per real customer, rule #1)', 96096,
           (SELECT COUNT(*) FROM dw.dim_customer)
    UNION ALL SELECT 'dim_product rows', 32951, (SELECT COUNT(*) FROM dw.dim_product)
    UNION ALL SELECT 'dim_seller rows', 3095, (SELECT COUNT(*) FROM dw.dim_seller)
    UNION ALL SELECT 'dim_order_status rows', 8, (SELECT COUNT(*) FROM dw.dim_order_status)
    UNION ALL SELECT 'fact_sales rows (one per item)', 112650, (SELECT COUNT(*) FROM dw.fact_sales)
    UNION ALL SELECT 'fact_orders rows (one per order, rule #16)', 99441,
           (SELECT COUNT(*) FROM dw.fact_orders)

    -- Missing dates must point to the -1 row, never be filled (rule #5)
    UNION ALL SELECT 'orders with missing approval date', 160,
           (SELECT COUNT(*) FROM dw.fact_orders WHERE approved_date_key = -1)
    UNION ALL SELECT 'orders with missing carrier date', 1783,
           (SELECT COUNT(*) FROM dw.fact_orders WHERE carrier_date_key = -1)
    UNION ALL SELECT 'orders with missing delivery date', 2965,
           (SELECT COUNT(*) FROM dw.fact_orders WHERE delivered_date_key = -1)

    -- Orders without items and delivery metrics (rules #3, #4, #16)
    UNION ALL SELECT 'orders without items', 775,
           (SELECT COUNT(*) FROM dw.fact_orders WHERE items_count = 0)
    UNION ALL SELECT 'orders with delivery metrics (delivered + date)', 96470,
           (SELECT COUNT(is_on_time) FROM dw.fact_orders)
    UNION ALL SELECT 'non-delivered orders with delivery metrics (must be 0)', 0,
           (SELECT COUNT(*) FROM dw.fact_orders
            WHERE order_status_key <> 1
              AND (is_on_time IS NOT NULL OR delivery_days IS NOT NULL OR delay_days IS NOT NULL))

    -- The two fact tables must agree with each other
    UNION ALL SELECT 'sum of items_count = rows of fact_sales', 112650,
           (SELECT SUM(items_count) FROM dw.fact_orders)
    UNION ALL SELECT 'items_total gap between the two facts, in cents (must be 0)', 0,
           (SELECT ROUND(ABS((SELECT SUM(items_total) FROM dw.fact_orders)
                           - (SELECT SUM(price + freight_value) FROM dw.fact_sales)) * 100)::bigint)

    -- Payments (rule #20): gaps above 1 cent
    UNION ALL SELECT 'payment vs items mismatch above 1 cent (rule #20)', 303,
           (SELECT COUNT(*) FROM dw.fact_orders
            WHERE items_total IS NOT NULL AND payment_total IS NOT NULL
              AND ABS(payment_total - items_total) > 0.01)

    -- Value sanity
    UNION ALL SELECT 'review_score outside 1-5 (must be 0)', 0,
           (SELECT COUNT(*) FROM dw.fact_orders WHERE review_score NOT BETWEEN 1 AND 5)
    UNION ALL SELECT 'negative delivery_days (must be 0)', 0,
           (SELECT COUNT(*) FROM dw.fact_orders WHERE delivery_days < 0)
)
SELECT check_name, expected, actual,
       CASE WHEN expected = actual THEN 'PASS' ELSE 'FAIL' END AS status
FROM checks;
