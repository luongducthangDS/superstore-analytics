-- Star schema tables for Power BI export.

CREATE OR REPLACE TABLE pbi_dim_product AS
SELECT
    product_id,
    max(product_name) AS product_name,
    max(category)     AS category,
    max(sub_category) AS sub_category
FROM fct_sales
GROUP BY product_id;

CREATE OR REPLACE TABLE pbi_dim_customer AS
SELECT
    customer_id,
    max(customer_name) AS customer_name,
    max(segment)       AS segment
FROM fct_sales
GROUP BY customer_id;

CREATE OR REPLACE TABLE pbi_dim_location AS
SELECT
    md5(state || '|' || city || '|' || postal_code) AS location_id,
    max(country)          AS country,
    max(region)           AS region,
    max(regional_manager) AS regional_manager,
    state,
    city,
    postal_code
FROM fct_sales
GROUP BY state, city, postal_code;

CREATE OR REPLACE TABLE pbi_dim_date AS
WITH bounds AS (
    SELECT min(order_date) AS min_d, max(order_date) AS max_d FROM fct_sales
),
dates AS (
    SELECT unnest(generate_series(min_d, max_d, INTERVAL 1 DAY))::DATE AS date
    FROM bounds
)
SELECT
    date,
    date_part('year', date)                             AS year,
    'Q' || date_part('quarter', date)                   AS quarter,
    date_part('month', date)                            AS month_num,
    strftime(date, '%B')                                AS month_name,
    strftime(date, '%Y-%m')                             AS year_month,
    strftime(date, '%A')                                AS day_name,
    date_part('isodow', date) IN (6, 7)                 AS is_weekend
FROM dates;

CREATE OR REPLACE TABLE pbi_fact_sales AS
SELECT
    s.row_id,
    s.order_id,
    s.order_date,
    s.customer_id,
    s.product_id,
    md5(s.state || '|' || s.city || '|' || s.postal_code) AS location_id,
    s.ship_mode,
    s.ship_days,
    s.sales,
    s.quantity,
    s.discount,
    s.profit,
    s.cogs,
    s.undiscounted_sales,
    s.discount_amount,
    s.profit_margin,
    s.is_loss,
    s.is_toxic_discount,
    s.discount_tier,
    s.is_returned
FROM fct_sales s;
