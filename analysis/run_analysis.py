"""Statistical and business analysis of Superstore sales & discount profitability.

Outputs:
- reports/results.json (reproducible metrics quoted in decision memo & README)
"""
import json
from pathlib import Path
import duckdb
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
REP = ROOT / "reports"
REP.mkdir(parents=True, exist_ok=True)


def load_model():
    con = duckdb.connect()
    con.execute("SET enable_progress_bar = false")
    con.execute(f"SET file_search_path = '{ROOT}'")
    con.execute((ROOT / "sql" / "00_model.sql").read_text())
    con.execute((ROOT / "sql" / "10_powerbi_export.sql").read_text())
    return con


def run():
    con = load_model()

    # 1. Headline KPIs
    kpi_query = """
    SELECT
        count(*)                                                    AS total_order_items,
        count(DISTINCT order_id)                                    AS total_orders,
        count(DISTINCT customer_id)                                 AS total_customers,
        round(sum(sales), 2)                                        AS gmv_sales,
        round(sum(profit), 2)                                       AS total_profit,
        round(sum(profit) / sum(sales) * 100, 2)                    AS profit_margin_pct,
        round(avg(discount) * 100, 2)                               AS avg_discount_pct,
        count(CASE WHEN is_loss THEN 1 END)                         AS loss_items_count,
        round(count(CASE WHEN is_loss THEN 1 END) * 100.0 / count(*), 2) AS loss_items_pct,
        round(abs(sum(CASE WHEN is_loss THEN profit ELSE 0 END)), 2) AS total_lost_dollars
    FROM fct_sales;
    """
    kpis = con.execute(kpi_query).fetchdf().to_dict(orient="records")[0]

    # 2. Discount Tier Analysis
    tier_query = """
    SELECT
        discount_tier,
        count(*)                                                    AS items,
        round(sum(sales), 2)                                        AS sales,
        round(sum(profit), 2)                                       AS profit,
        round(sum(profit) / sum(sales) * 100, 2)                    AS margin_pct,
        round(count(CASE WHEN is_loss THEN 1 END) * 100.0 / count(*), 2) AS loss_rate_pct
    FROM fct_sales
    GROUP BY discount_tier
    ORDER BY min(discount);
    """
    discount_tiers = con.execute(tier_query).fetchdf().to_dict(orient="records")

    # 3. Regional and Category Breakdown (Identifying Central Region Furniture Drain)
    regional_query = """
    SELECT
        region,
        regional_manager,
        count(*)                                                    AS items,
        round(sum(sales), 2)                                        AS sales,
        round(sum(profit), 2)                                       AS profit,
        round(sum(profit) / sum(sales) * 100, 2)                    AS margin_pct,
        round(avg(discount) * 100, 2)                               AS avg_discount_pct,
        round(sum(CASE WHEN is_loss THEN profit ELSE 0 END), 2)     AS total_loss_dollars
    FROM fct_sales
    GROUP BY region, regional_manager
    ORDER BY profit ASC;
    """
    regions = con.execute(regional_query).fetchdf().to_dict(orient="records")

    # 4. Toxic Sub-Categories: Tables, Bookcases, Supplies
    subcat_query = """
    SELECT
        sub_category,
        category,
        count(*)                                                    AS items,
        round(sum(sales), 2)                                        AS sales,
        round(sum(profit), 2)                                       AS profit,
        round(sum(profit) / sum(sales) * 100, 2)                    AS margin_pct,
        round(avg(discount) * 100, 2)                               AS avg_discount_pct,
        round(sum(CASE WHEN is_loss THEN profit ELSE 0 END), 2)     AS loss_dollars
    FROM fct_sales
    GROUP BY sub_category, category
    ORDER BY profit ASC;
    """
    subcats = con.execute(subcat_query).fetchdf().to_dict(orient="records")

    # 5. Break-even Discount calculation per Sub-Category via linear regression
    # Profit = alpha + beta * Discount -> Break-even = -alpha / beta
    thresholds = []
    subcat_names = con.execute("SELECT DISTINCT sub_category FROM fct_sales").fetchall()
    for (sc,) in subcat_names:
        reg = con.execute(f"""
            SELECT
                regr_intercept(profit, discount) AS alpha,
                regr_slope(profit, discount)     AS beta,
                regr_r2(profit, discount)        AS r2,
                avg(discount)                    AS cur_discount,
                sum(profit)                      AS total_profit,
                sum(CASE WHEN is_loss THEN profit ELSE 0 END) AS subcat_loss
            FROM fct_sales
            WHERE sub_category = '{sc}'
        """).fetchone()
        alpha, beta, r2, cur_disc, tot_prof, sub_loss = reg
        if beta is not None and beta < -1.0 and alpha > 0:
            break_even = -alpha / beta
            thresholds.append({
                "sub_category": sc,
                "break_even_discount_pct": round(break_even * 100, 1),
                "current_avg_discount_pct": round(cur_disc * 100, 1),
                "r2": round(r2, 3),
                "total_profit": round(tot_prof, 2),
                "total_loss": round(sub_loss, 2)
            })

    thresholds.sort(key=lambda x: x["total_loss"])

    # 6. OLS Regression with HC3 Robust Standard Errors
    # Model: profit = beta0 + beta1 * discount + beta2 * discount^2 + beta3 * sales
    reg_data = con.execute("""
        SELECT profit, discount, discount * discount AS disc_sq, sales
        FROM fct_sales
    """).fetchall()

    y = np.array([r[0] for r in reg_data])
    X = np.column_stack([
        np.ones(len(reg_data)),
        [r[1] for r in reg_data],
        [r[2] for r in reg_data],
        [r[3] for r in reg_data],
    ])

    # OLS coefficients
    XtX_inv = np.linalg.pinv(X.T @ X)
    beta = XtX_inv @ (X.T @ y)
    residuals = y - X @ beta

    # HC3 Robust Covariance: e_i^2 / (1 - h_ii)^2
    H = np.sum(X * (X @ XtX_inv), axis=1)  # leverage h_ii
    H = np.clip(H, 0, 0.999)
    w = (residuals / (1.0 - H)) ** 2
    meat = X.T @ (X * w[:, None])
    vcov_hc3 = XtX_inv @ meat @ XtX_inv
    se_hc3 = np.sqrt(np.diag(vcov_hc3))

    results = {
        "kpis": kpis,
        "discount_tiers": discount_tiers,
        "regions": regions,
        "bottom_subcategories": subcats[:5],
        "toxic_thresholds": thresholds[:5],
        "regression": {
            "intercept": round(float(beta[0]), 3),
            "discount_linear_coef": round(float(beta[1]), 3),
            "discount_linear_se_hc3": round(float(se_hc3[1]), 3),
            "discount_quad_coef": round(float(beta[2]), 3),
            "discount_quad_se_hc3": round(float(se_hc3[2]), 3),
            "sales_coef": round(float(beta[3]), 4),
            "sales_se_hc3": round(float(se_hc3[3]), 4),
        }
    }

    out_file = REP / "results.json"
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"Analysis completed successfully! Results written to {out_file}")
    print("\n--- Headline Summary ---")
    print(f"Total Sales: ${kpis['gmv_sales']:,.2f} | Total Profit: ${kpis['total_profit']:,.2f} ({kpis['profit_margin_pct']}%)")
    print(f"Loss-making order items: {kpis['loss_items_pct']}% of items, losing -${kpis['total_lost_dollars']:,.2f}")
    print(f"Central region manager ({regions[0]['regional_manager']}) margin: {regions[0]['margin_pct']}% vs West {regions[-1]['margin_pct']}%")


if __name__ == "__main__":
    run()
