"""Build Power BI star schema CSVs and an interactive Plotly HTML dashboard.

Outputs:
- powerbi/*.csv (Ready to load into Power BI Desktop)
- reports/dashboard.html (Standalone interactive visual dashboard)
"""
from pathlib import Path
import duckdb
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROOT = Path(__file__).resolve().parents[1]
PBI = ROOT / "powerbi"
REP = ROOT / "reports"
PBI.mkdir(parents=True, exist_ok=True)
REP.mkdir(parents=True, exist_ok=True)


def main():
    con = duckdb.connect()
    con.execute("SET enable_progress_bar = false")
    con.execute(f"SET file_search_path = '{ROOT}'")
    con.execute((ROOT / "sql" / "00_model.sql").read_text())
    con.execute((ROOT / "sql" / "10_powerbi_export.sql").read_text())

    # 1. Export Power BI CSVs
    pbi_tables = [
        ("pbi_fact_sales", "fact_sales.csv"),
        ("pbi_dim_product", "dim_product.csv"),
        ("pbi_dim_customer", "dim_customer.csv"),
        ("pbi_dim_location", "dim_location.csv"),
        ("pbi_dim_date", "dim_date.csv"),
    ]
    for tbl, fname in pbi_tables:
        csv_path = (PBI / fname).as_posix()
        con.execute(f"COPY {tbl} TO '{csv_path}' (HEADER, DELIMITER ',')")
        print(f"Exported {tbl} -> {PBI / fname}")

    # 2. Build Interactive HTML Dashboard
    df_tiers = con.execute("""
        SELECT
            discount_tier,
            sum(sales) AS total_sales,
            sum(profit) AS total_profit,
            round(sum(profit)/sum(sales)*100, 2) AS margin_pct,
            round(count(CASE WHEN is_loss THEN 1 END)*100.0/count(*), 2) AS loss_rate
        FROM fct_sales
        GROUP BY discount_tier
        ORDER BY min(discount)
    """).fetchdf()

    df_subcat = con.execute("""
        SELECT
            sub_category,
            sum(sales) AS sales,
            sum(profit) AS profit,
            round(avg(discount)*100, 1) AS avg_disc,
            category
        FROM fct_sales
        GROUP BY sub_category, category
        ORDER BY profit ASC
    """).fetchdf()

    df_region = con.execute("""
        SELECT
            region,
            sum(sales) AS sales,
            sum(profit) AS profit,
            round(sum(profit)/sum(sales)*100, 2) AS margin_pct
        FROM fct_sales
        GROUP BY region
        ORDER BY margin_pct ASC
    """).fetchdf()

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Profit Margin by Discount Tier (The Toxic Cliff)",
            "Regional Profit Margin (Central vs West)",
            "Sub-Category Profitability vs Average Discount",
            "Cumulative Sales vs Negative Profit Drain"
        ),
        specs=[[{"type": "bar"}, {"type": "bar"}],
               [{"type": "scatter"}, {"type": "bar"}]]
    )

    # 1. Discount Tier Margins
    fig.add_trace(
        go.Bar(
            x=df_tiers["discount_tier"],
            y=df_tiers["margin_pct"],
            text=df_tiers["margin_pct"].apply(lambda x: f"{x}%"),
            textposition="auto",
            marker_color=["#10B981", "#3B82F6", "#F59E0B", "#EF4444"],
            name="Margin %"
        ),
        row=1, col=1
    )

    # 2. Regional Margin
    fig.add_trace(
        go.Bar(
            x=df_region["region"],
            y=df_region["margin_pct"],
            text=df_region["margin_pct"].apply(lambda x: f"{x}%"),
            textposition="auto",
            marker_color="#6366F1",
            name="Regional Margin"
        ),
        row=1, col=2
    )

    # 3. Scatter: Profit vs Discount by Sub-Category
    fig.add_trace(
        go.Scatter(
            x=df_subcat["avg_disc"],
            y=df_subcat["profit"],
            mode="markers+text",
            text=df_subcat["sub_category"],
            textposition="top center",
            marker=dict(
                size=df_subcat["sales"] / 15000 + 8,
                color=df_subcat["profit"],
                colorscale="RdYlGn",
                showscale=True,
                colorbar=dict(title="Profit ($)", x=1.05)
            ),
            name="Sub-Categories"
        ),
        row=2, col=1
    )

    # 4. Bottom Subcategories by Profit
    worst_5 = df_subcat.head(5)
    fig.add_trace(
        go.Bar(
            x=worst_5["sub_category"],
            y=worst_5["profit"],
            text=worst_5["profit"].apply(lambda x: f"${x:,.0f}"),
            textposition="auto",
            marker_color="#DC2626",
            name="Loss Leaders"
        ),
        row=2, col=2
    )

    fig.update_layout(
        title_text="<b>Superstore Sales & Profitability Executive Dashboard</b><br><sup>Does discounting drive volume at the expense of bottom-line profit?</sup>",
        template="plotly_white",
        height=850,
        showlegend=False
    )

    dashboard_path = REP / "dashboard.html"
    fig.write_html(str(dashboard_path), include_plotlyjs="cdn")
    print(f"Generated interactive dashboard: {dashboard_path}")


if __name__ == "__main__":
    main()
