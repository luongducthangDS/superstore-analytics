# Power BI Rebuild Guide: Superstore Sales & Profitability

This directory contains the cleaned, typed star schema CSVs generated from `sql/10_powerbi_export.sql` by running `python analysis/build_dashboard.py`.

## Data Model & Relationships

1. Load the 5 CSV files:
   - `fact_sales.csv` (9,994 rows)
   - `dim_product.csv` (1,862 distinct products)
   - `dim_customer.csv` (793 distinct customers)
   - `dim_location.csv` (604 distinct geographic locations)
   - `dim_date.csv` (Full calendar covering order dates)

2. Create 1-to-many relationships (Single direction filter, 1 dimension to * fact):
   - `dim_date[date]` 1 ---> * `fact_sales[order_date]`
   - `dim_product[product_id]` 1 ---> * `fact_sales[product_id]`
   - `dim_customer[customer_id]` 1 ---> * `fact_sales[customer_id]`
   - `dim_location[location_id]` 1 ---> * `fact_sales[location_id]`

3. Create DAX measures from `measures.dax`.
