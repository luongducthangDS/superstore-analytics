# Superstore: Does Discounting Drive Volume at the Cost of Profit?

Analysis of **9,994 order line items** ($2.30M gross sales) from the Tableau Sample Superstore dataset. It starts from a fundamental business question, models the data in DuckDB SQL, evaluates non-linear discount elasticity with econometric statistics, and delivers a [one-page decision memo](docs/decision_memo.md) and an interactive dashboard.

![Dashboard](reports/figures/00_dashboard_preview.png)

## Executive Answer

**Yes.** Sales discounts are destroying more value than they create. While revenue grew 20% YoY, deep discounts (>20%) caused **$156,132 in net bottom-line losses** across 1,871 order items. The erosion is heavily concentrated in specific sub-categories (*Tables*, *Bookcases*) and the Central sales region.

| Finding | Value |
|---|---|
| Total Gross Sales | **$2,297,201.03** across 5,009 orders & 793 customers |
| Total Net Profit & Margin | **$286,397.61** (12.47% overall margin) |
| Loss-making Order Items | **18.72% of items** (1,871 items), producing **-$156,132** in gross losses |
| 0% Discount Profit Margin | **+29.9%** (healthy unit economics) |
| >20% Toxic Discount Margin | **-38.2%** (catastrophic margin collapse) |
| Break-even Discount (Tables) | **16.2%**; current average discount is 26.1% |
| Central Region Profit Margin | **7.92%** (worst region) vs. West at **14.94%** |
| Central Region Furniture Losses | **-$17,725.32** under Regional Manager Kelly Williams |
| Return Rate Impact | 8.0% of orders returned; returns exacerbate losses on discounted goods |

**So what:** Impose an immediate 15% hard-cap on discounts for *Tables* and *Bookcases*, and restructure B2B contract terms in Texas and Illinois. This recovers **$42k–$65k annually** with zero impact on healthy baseline demand.

## Architecture & Method

1. **Model** (`sql/00_model.sql`, DuckDB): Grain is 1 row per order item. Reconciles COGS, calculates list price undiscounted sales, flags toxic discounts (>20%), and joins regional manager metadata and order return status.
2. **Checks** (`tests/test_model.py`, pytest): 7 automated tests verifying row counts (9,994), zero null metrics, exact COGS reconciliation, discount tier definitions, dimension surrogate keys, and referential integrity.
3. **Analysis** (`analysis/run_analysis.py`):
   - Discount tier bucketing (0%, 1-10%, 11-20%, >20%).
   - Break-even discount threshold derivation per sub-category via linear regression ($Profit = \alpha + \beta \cdot Discount \implies \text{Break-even} = -\alpha/\beta$).
   - OLS regression with HC3 heteroskedasticity-consistent robust standard errors controlling for sales volume and quadratic discount effects.
4. **Outputs**:
   - `reports/results.json` (reproducible metrics).
   - `reports/dashboard.html` (interactive Plotly dashboard).
   - `powerbi/`: Star schema CSVs (`fact_sales.csv`, `dim_product.csv`, `dim_customer.csv`, `dim_location.csv`, `dim_date.csv`), `measures.dax`, and `power_query.m`.

## How to Run It

```bash
pip install -r requirements.txt
python scripts/get_data.py              # Fetches and separates raw orders, people, and returns
pytest -q                               # Runs 7 data integrity and referential checks
python analysis/run_analysis.py         # Generates reports/results.json
python analysis/build_dashboard.py      # Exports powerbi/*.csv & reports/dashboard.html
```

## Decisions Worth Defending in an Interview

- **Why focus on break-even discount rather than banning all discounts?** Banning discounts entirely destroys demand elasticity and causes inventory holding costs to balloon. Sub-20% discounts generate positive margins (+18% to +29%). The goal is pruning **toxic discounting (>20%)**, not killing top-line volume.
- **Why use HC3 robust standard errors?** In sales and transaction data, variance of profit increases with larger transaction sizes (heteroskedasticity). Standard OLS standard errors underestimate variance, leading to artificially low p-values. HC3 guarantees confidence intervals remain valid.
- **Why a Star Schema with an MD5 location surrogate key?** Postal codes in the US are not guaranteed unique across cities or can have missing values. Creating a composite MD5 hash (`state | city | postal_code`) ensures 100% unique primary keys in `dim_location` and prevents many-to-many relationship traps in Power BI.

## Interview Questions this Project Prepares For

1. How did you identify the break-even discount rate, and why is the relationship between discount and profit non-linear?
2. If the Central region has low profit margin, how do you verify whether it's caused by sales reps giving excessive discounts versus high logistics/shipping costs?
3. How would you design an A/B test or pilot program to test capping discounts at 15% without hurting customer retention?
