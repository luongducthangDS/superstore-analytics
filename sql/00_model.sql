-- Sales & Profitability Analysis Model: One row per order item.
-- Built in DuckDB from data/raw/raw_orders.csv, raw_people.csv, raw_returns.csv.

CREATE OR REPLACE TABLE dim_returns AS
SELECT DISTINCT "Order ID" AS order_id
FROM read_csv_auto('data/raw/raw_returns.csv');

CREATE OR REPLACE TABLE dim_people AS
SELECT TRIM("Person") AS regional_manager, TRIM("Region") AS region
FROM read_csv_auto('data/raw/raw_people.csv');

CREATE OR REPLACE TABLE fct_sales AS
WITH raw_data AS (
    SELECT
        "Row ID"                                                        AS row_id,
        TRIM("Order ID")                                                AS order_id,
        CAST("Order Date" AS DATE)                                      AS order_date,
        CAST("Ship Date" AS DATE)                                       AS ship_date,
        date_diff('day', CAST("Order Date" AS DATE), CAST("Ship Date" AS DATE)) AS ship_days,
        TRIM("Ship Mode")                                               AS ship_mode,
        TRIM("Customer ID")                                             AS customer_id,
        TRIM("Customer Name")                                           AS customer_name,
        TRIM("Segment")                                                 AS segment,
        TRIM("Country")                                                 AS country,
        TRIM("City")                                                    AS city,
        TRIM("State")                                                   AS state,
        COALESCE(NULLIF(TRIM(CAST("Postal Code" AS VARCHAR)), ''), 'N/A') AS postal_code,
        TRIM("Region")                                                  AS region,
        TRIM("Product ID")                                              AS product_id,
        TRIM("Category")                                                AS category,
        TRIM("Sub-Category")                                            AS sub_category,
        TRIM("Product Name")                                            AS product_name,
        ROUND(CAST("Sales" AS DOUBLE), 2)                               AS sales,
        CAST("Quantity" AS INTEGER)                                     AS quantity,
        ROUND(CAST("Discount" AS DOUBLE), 2)                             AS discount,
        ROUND(CAST("Profit" AS DOUBLE), 2)                              AS profit
    FROM read_csv_auto('data/raw/raw_orders.csv')
)
SELECT
    r.row_id,
    r.order_id,
    r.order_date,
    date_trunc('month', r.order_date)::DATE                             AS order_month,
    r.ship_date,
    r.ship_days,
    r.ship_mode,
    r.customer_id,
    r.customer_name,
    r.segment,
    r.country,
    r.city,
    r.state,
    r.postal_code,
    r.region,
    p.regional_manager,
    r.product_id,
    r.category,
    r.sub_category,
    r.product_name,
    r.sales,
    r.quantity,
    r.discount,
    r.profit,
    ROUND(r.sales - r.profit, 2)                                        AS cogs,
    ROUND(CASE WHEN r.discount < 1.0 THEN r.sales / (1.0 - r.discount) ELSE r.sales END, 2) AS undiscounted_sales,
    ROUND(CASE WHEN r.discount < 1.0 THEN (r.sales / (1.0 - r.discount)) * r.discount ELSE 0 END, 2) AS discount_amount,
    ROUND(r.profit / NULLIF(r.sales, 0), 4)                             AS profit_margin,
    r.profit < 0                                                        AS is_loss,
    r.discount > 0.20                                                   AS is_toxic_discount,
    CASE
        WHEN r.discount = 0 THEN '0% None'
        WHEN r.discount <= 0.10 THEN '1-10% Low'
        WHEN r.discount <= 0.20 THEN '11-20% Moderate'
        ELSE '>20% Toxic'
    END                                                                 AS discount_tier,
    ret.order_id IS NOT NULL                                            AS is_returned
FROM raw_data r
LEFT JOIN dim_people p USING (region)
LEFT JOIN dim_returns ret USING (order_id);
