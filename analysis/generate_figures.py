"""Generate publication-quality figures for Superstore analytics README."""
from pathlib import Path
import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

INK, MUTED, GRID = "#1F2937", "#6B7280", "#E5E7EB"
BLUE, RED, GREEN, AMBER = "#2563EB", "#DC2626", "#059669", "#D97706"

plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 10,
    "axes.edgecolor": GRID,
    "axes.labelcolor": MUTED,
    "xtick.color": MUTED,
    "ytick.color": MUTED,
    "axes.titlelocation": "left",
    "axes.titleweight": "bold",
    "axes.titlecolor": INK
})


def generate():
    con = duckdb.connect()
    con.execute("SET enable_progress_bar = false")
    con.execute(f"SET file_search_path = '{ROOT}'")
    con.execute((ROOT / "sql" / "00_model.sql").read_text())

    # 1. Dashboard Preview (4 panels)
    fig, axes = plt.subplots(2, 2, figsize=(14, 9), dpi=150)
    fig.patch.set_facecolor("#FAFAFA")
    for ax in axes.flat:
        ax.set_facecolor("white")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color=GRID, linestyle="--", alpha=0.7)
        ax.set_axisbelow(True)

    # Panel 1: Discount Tiers
    tiers = con.execute("""
        SELECT discount_tier, round(sum(profit)/sum(sales)*100, 1) AS margin
        FROM fct_sales
        GROUP BY discount_tier
        ORDER BY min(discount)
    """).fetchall()
    x1 = [t[0] for t in tiers]
    y1 = [t[1] for t in tiers]
    c1 = [GREEN, BLUE, AMBER, RED]
    bars1 = axes[0, 0].bar(x1, y1, color=c1, width=0.55, edgecolor="none", zorder=3)
    axes[0, 0].set_title("A. Profit Margin Collapse by Discount Tier")
    axes[0, 0].set_ylabel("Net Profit Margin (%)")
    axes[0, 0].axhline(0, color=INK, linewidth=1, linestyle="-")
    for b in bars1:
        h = b.get_height()
        va = "bottom" if h >= 0 else "top"
        axes[0, 0].text(b.get_x() + b.get_width() / 2, h + (1.5 if h >= 0 else -3),
                        f"{h:+.1f}%", ha="center", va=va, fontweight="bold", fontsize=10,
                        color=GREEN if h > 0 else RED)

    # Panel 2: Regional Margin Gap
    regions = con.execute("""
        SELECT region, round(sum(profit)/sum(sales)*100, 1) AS margin, round(sum(sales)/1000, 0) AS sales_k
        FROM fct_sales
        GROUP BY region
        ORDER BY margin ASC
    """).fetchall()
    x2 = [r[0] for r in regions]
    y2 = [r[1] for r in regions]
    c2 = [RED if r[0] == "Central" else BLUE for r in regions]
    bars2 = axes[0, 1].bar(x2, y2, color=c2, width=0.55, zorder=3)
    axes[0, 1].set_title("B. Regional Profit Margin (Central vs West)")
    axes[0, 1].set_ylabel("Profit Margin (%)")
    for b in bars2:
        h = b.get_height()
        axes[0, 1].text(b.get_x() + b.get_width() / 2, h + 0.6,
                        f"{h:.1f}%", ha="center", va="bottom", fontweight="bold", color=INK)

    # Panel 3: Sub-Category Profit vs Average Discount
    subcats = con.execute("""
        SELECT sub_category, round(avg(discount)*100, 1) AS avg_disc, round(sum(profit), 0) AS profit, category
        FROM fct_sales
        GROUP BY sub_category, category
    """).fetchall()
    for sc, disc, prof, cat in subcats:
        c = RED if prof < 0 else (GREEN if prof > 20000 else BLUE)
        axes[1, 0].scatter(disc, prof, s=120, color=c, alpha=0.85, edgecolors=INK, linewidths=0.5, zorder=3)
        if prof < 0 or prof > 25000:
            axes[1, 0].text(disc + 0.5, prof, sc, fontsize=9, fontweight="bold", color=c)
    axes[1, 0].axhline(0, color=INK, linewidth=1, linestyle="--")
    axes[1, 0].set_title("C. Sub-Category Profitability vs Avg Discount Rate")
    axes[1, 0].set_xlabel("Average Discount Rate (%)")
    axes[1, 0].set_ylabel("Total Net Profit ($)")

    # Panel 4: Break-Even Discount Curve for Tables
    tables_data = con.execute("""
        SELECT discount, profit FROM fct_sales WHERE sub_category = 'Tables'
    """).fetchall()
    td_x = np.array([r[0] * 100 for r in tables_data])
    td_y = np.array([r[1] for r in tables_data])
    axes[1, 1].scatter(td_x, td_y, color="#9CA3AF", alpha=0.4, s=25, label="Order Items", zorder=2)
    # Regression line
    p = np.polyfit(td_x, td_y, 1)
    x_line = np.linspace(0, 70, 100)
    y_line = np.polyval(p, x_line)
    break_even = -p[1] / p[0]
    axes[1, 1].plot(x_line, y_line, color=RED, linewidth=2.5, label="Fitted OLS Trend", zorder=3)
    axes[1, 1].axhline(0, color=INK, linewidth=1, linestyle="-")
    axes[1, 1].axvline(break_even, color=AMBER, linewidth=1.5, linestyle=":", label=f"Break-even: {break_even:.1f}%")
    axes[1, 1].scatter([break_even], [0], color=RED, s=150, zorder=4)
    axes[1, 1].set_title("D. Tables: Point of Negative Margin (Break-Even = 16.2%)")
    axes[1, 1].set_xlabel("Discount Rate (%)")
    axes[1, 1].set_ylabel("Item Net Profit ($)")
    axes[1, 1].legend(loc="upper right", frameon=True, fontsize=8.5)

    fig.suptitle("SUPERSTORE PROFITABILITY & DISCOUNT ELASTICITY DASHBOARD",
                 fontsize=14, fontweight="bold", y=0.98, color=INK)
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    out1 = FIG / "00_dashboard_preview.png"
    fig.savefig(out1, dpi=150)
    plt.close(fig)
    print(f"Generated {out1}")


if __name__ == "__main__":
    generate()
