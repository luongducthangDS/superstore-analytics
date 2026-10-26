"""Generate publication-quality figures for Superstore analytics README.
Generates:
- 00_dashboard_preview.png (Composite 4-panel executive overview, zero collision)
- 01_discount_cliff_margin.png (Standalone: Profit margin collapse across discount tiers)
- 02_subcategory_profit_matrix.png (Standalone: Net Profit vs Sales Volume with non-overlapping labels)
- 03_tables_breakeven_regression.png (Standalone: Tables break-even discount curve)
"""
from pathlib import Path
import duckdb
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FIG = ROOT / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

INK, MUTED, GRID = "#111827", "#4B5563", "#E5E7EB"
BLUE, RED, GREEN, AMBER, PURPLE = "#1D4ED8", "#DC2626", "#059669", "#D97706", "#7C3AED"

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

    # =========================================================================
    # 1. COMPOSITE DASHBOARD PREVIEW (00_dashboard_preview.png)
    # =========================================================================
    fig, axes = plt.subplots(2, 2, figsize=(15, 9.8), dpi=160)
    fig.patch.set_facecolor("#FAFAFA")
    for ax in axes.flat:
        ax.set_facecolor("white")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color=GRID, linestyle="--", alpha=0.7)
        ax.set_axisbelow(True)

    # Panel A: Discount Tiers
    tiers = con.execute("""
        SELECT discount_tier, round(sum(profit)/sum(sales)*100, 1) AS margin, sum(profit) as tot_profit
        FROM fct_sales
        GROUP BY discount_tier
        ORDER BY min(discount)
    """).fetchall()
    x1 = [t[0].replace(" Discount", "").replace(" Price", "") for t in tiers]
    y1 = [t[1] for t in tiers]
    c1 = [GREEN, BLUE, AMBER, RED]
    bars1 = axes[0, 0].bar(x1, y1, color=c1, width=0.52, zorder=3)
    axes[0, 0].set_title("A. Profit Margin Collapse by Discount Tier")
    axes[0, 0].set_ylabel("Net Profit Margin (%)")
    axes[0, 0].set_ylim(-48, 42)
    axes[0, 0].axhline(0, color=INK, linewidth=1, linestyle="-")
    for b in bars1:
        h = b.get_height()
        va = "bottom" if h >= 0 else "top"
        y_offset = h + 1.8 if h >= 0 else h - 2.5
        axes[0, 0].text(b.get_x() + b.get_width() / 2, y_offset,
                        f"{h:+.1f}%", ha="center", va=va, fontweight="bold", fontsize=9.5,
                        color=GREEN if h > 0 else RED)

    # Panel B: Regional Profit Margin
    regions = con.execute("""
        SELECT region, round(sum(profit)/sum(sales)*100, 1) AS margin, round(sum(profit)/1000, 1) as profit_k
        FROM fct_sales
        GROUP BY region
        ORDER BY margin ASC
    """).fetchall()
    x2 = [r[0] for r in regions]
    y2 = [r[1] for r in regions]
    c2 = [RED if r[0] == "Central" else BLUE for r in regions]
    bars2 = axes[0, 1].bar(x2, y2, color=c2, width=0.52, zorder=3)
    axes[0, 1].set_title("B. Regional Profit Margin (Central Drain)")
    axes[0, 1].set_ylabel("Profit Margin (%)")
    axes[0, 1].set_ylim(0, 20)
    for b, r in zip(bars2, regions):
        h = b.get_height()
        axes[0, 1].text(b.get_x() + b.get_width() / 2, h + 0.6,
                        f"{h:.1f}%\n(${r[2]:.1f}k)", ha="center", va="bottom",
                        fontsize=9, fontweight="bold", color=INK)

    # Panel C: Sub-Category Profitability Scatter (With non-overlapping labels)
    subcats = con.execute("""
        SELECT sub_category, round(avg(discount)*100, 1) AS avg_disc, round(sum(profit), 0) AS profit, category
        FROM fct_sales
        GROUP BY sub_category, category
    """).fetchall()
    for sc, disc, prof, cat in subcats:
        c = RED if prof < 0 else (GREEN if prof > 25000 else BLUE)
        axes[1, 0].scatter(disc, prof, s=110, color=c, alpha=0.85, edgecolors=INK, linewidths=0.5, zorder=3)

    # Smart explicit annotations to completely prevent collision
    annotations_c = {
        "Tables": (1.2, 0, RED, "left"),
        "Bookcases": (1.2, 0, RED, "left"),
        "Supplies": (-0.8, -2500, RED, "right"),
        "Copiers": (1.2, 0, GREEN, "left"),
        "Phones": (1.2, 0, GREEN, "left"),
        "Accessories": (1.2, 0, GREEN, "left"),
        "Paper": (1.2, 0, BLUE, "left"),
        "Binders": (-1.0, 2500, BLUE, "right"),
        "Chairs": (1.2, 0, BLUE, "left"),
        "Appliances": (1.2, 0, BLUE, "left"),
        "Storage": (1.2, 0, BLUE, "left"),
    }
    for sc, disc, prof, cat in subcats:
        if sc in annotations_c:
            dx, dy, col, ha = annotations_c[sc]
            axes[1, 0].text(disc + dx, prof + dy, sc, fontsize=8.5, fontweight="bold", color=col, ha=ha, va="center")

    axes[1, 0].axhline(0, color=INK, linewidth=1, linestyle="--")
    axes[1, 0].set_title("C. Sub-Category Profit vs Average Discount Rate")
    axes[1, 0].set_xlabel("Average Discount Rate (%)")
    axes[1, 0].set_ylabel("Total Net Profit ($)")
    axes[1, 0].set_ylim(-24000, 64000)
    axes[1, 0].set_xlim(4, 42)

    # Panel D: Tables Break-Even Curve
    tables_data = con.execute("""
        SELECT discount, profit FROM fct_sales WHERE sub_category = 'Tables'
    """).fetchall()
    td_x = np.array([r[0] * 100 for r in tables_data])
    td_y = np.array([r[1] for r in tables_data])
    axes[1, 1].scatter(td_x, td_y, color="#9CA3AF", alpha=0.35, s=25, label="Order Items", zorder=2)
    p = np.polyfit(td_x, td_y, 1)
    x_line = np.linspace(0, 70, 100)
    y_line = np.polyval(p, x_line)
    break_even = -p[1] / p[0]
    axes[1, 1].plot(x_line, y_line, color=RED, linewidth=2.5, label="Fitted OLS Trend", zorder=3)
    axes[1, 1].axhline(0, color=INK, linewidth=1, linestyle="-")
    axes[1, 1].axvline(break_even, color=AMBER, linewidth=1.5, linestyle=":", label=f"Break-even: {break_even:.1f}%")
    axes[1, 1].scatter([break_even], [0], color=RED, s=140, zorder=4)
    axes[1, 1].set_title(f"D. Tables: Point of Negative Margin (Break-Even = {break_even:.1f}%)")
    axes[1, 1].set_xlabel("Discount Rate (%)")
    axes[1, 1].set_ylabel("Item Net Profit ($)")
    axes[1, 1].legend(loc="upper right", frameon=True, fontsize=8.5)

    fig.suptitle("SUPERSTORE PROFITABILITY & DISCOUNT ELASTICITY DASHBOARD",
                 fontsize=14, fontweight="bold", y=0.98, color=INK)
    fig.subplots_adjust(top=0.92, bottom=0.08, left=0.08, right=0.96, hspace=0.34, wspace=0.25)
    out0 = FIG / "00_dashboard_preview.png"
    fig.savefig(out0, dpi=160)
    plt.close(fig)
    print(f"Generated {out0}")

    # =========================================================================
    # 2. STANDALONE FIGURE 1: DISCOUNT CLIFF MARGIN (01_discount_cliff_margin.png)
    # =========================================================================
    fig1, ax1 = plt.subplots(figsize=(10, 5.5), dpi=160)
    fig1.patch.set_facecolor("white")
    ax1.set_facecolor("white")
    ax1.spines[["top", "right"]].set_visible(False)
    ax1.grid(axis="y", color=GRID, linestyle="--", alpha=0.7)
    ax1.set_axisbelow(True)

    b1 = ax1.bar(x1, y1, color=c1, width=0.5, zorder=3)
    ax1.axhline(0, color=INK, linewidth=1.2)
    ax1.set_title("The Toxic Discount Cliff: Margin Collapse at >20% Discount", fontsize=12, pad=12)
    ax1.set_ylabel("Net Profit Margin (%)", fontsize=10)
    ax1.set_ylim(-48, 42)

    for b, t in zip(b1, tiers):
        h = b.get_height()
        va = "bottom" if h >= 0 else "top"
        y_pos = h + 1.8 if h >= 0 else h - 2.5
        profit_str = f"Profit: +${t[2]:,.0f}" if t[2] >= 0 else f"Loss: -${abs(t[2]):,.0f}"
        ax1.text(b.get_x() + b.get_width() / 2, y_pos,
                 f"{h:+.1f}%\n({profit_str})", ha="center", va=va,
                 fontweight="bold", fontsize=9.5, color=GREEN if h > 0 else RED)

    fig1.tight_layout()
    out1 = FIG / "01_discount_cliff_margin.png"
    fig1.savefig(out1, dpi=160)
    plt.close(fig1)
    print(f"Generated {out1}")

    # =========================================================================
    # 3. STANDALONE FIGURE 2: SUB-CATEGORY PROFIT MATRIX (02_subcategory_profit_matrix.png)
    # =========================================================================
    fig2, ax2 = plt.subplots(figsize=(11, 6), dpi=160)
    fig2.patch.set_facecolor("white")
    ax2.set_facecolor("white")
    ax2.spines[["top", "right"]].set_visible(False)
    ax2.grid(True, color=GRID, linestyle="--", alpha=0.7)
    ax2.set_axisbelow(True)

    for sc, disc, prof, cat in subcats:
        c = RED if prof < 0 else (GREEN if prof > 25000 else BLUE)
        ax2.scatter(disc, prof, s=130, color=c, alpha=0.85, edgecolors=INK, linewidths=0.5, zorder=3)

    annotations_stand = {
        "Tables": (1.2, 0, RED, "left"),
        "Bookcases": (1.2, 0, RED, "left"),
        "Supplies": (-0.8, -2500, RED, "right"),
        "Copiers": (1.2, 0, GREEN, "left"),
        "Phones": (1.2, 0, GREEN, "left"),
        "Accessories": (1.2, 0, GREEN, "left"),
        "Paper": (1.2, 0, BLUE, "left"),
        "Binders": (-1.0, 2500, BLUE, "right"),
        "Storage": (1.2, 0, BLUE, "left"),
        "Appliances": (1.2, 0, BLUE, "left"),
        "Chairs": (1.2, 0, BLUE, "left"),
    }
    for sc, disc, prof, cat in subcats:
        if sc in annotations_stand:
            dx, dy, col, ha = annotations_stand[sc]
            ax2.text(disc + dx, prof + dy, sc, fontsize=9, fontweight="bold", color=col, ha=ha, va="center")

    ax2.axhline(0, color=INK, linewidth=1.2, linestyle="--")
    ax2.set_title("Value Destruction vs Creation: Sub-Category Profitability vs Average Discount", fontsize=12, pad=12)
    ax2.set_xlabel("Average Discount Rate (%)", fontsize=10)
    ax2.set_ylabel("Total Net Profit ($)", fontsize=10)
    ax2.set_ylim(-24000, 64000)
    ax2.set_xlim(4, 42)
    fig2.tight_layout()
    out2 = FIG / "02_subcategory_profit_matrix.png"
    fig2.savefig(out2, dpi=160)
    plt.close(fig2)
    print(f"Generated {out2}")

    # =========================================================================
    # 4. STANDALONE FIGURE 3: TABLES BREAK-EVEN REGRESSION (03_tables_breakeven_regression.png)
    # =========================================================================
    fig3, ax3 = plt.subplots(figsize=(10, 5.5), dpi=160)
    fig3.patch.set_facecolor("white")
    ax3.set_facecolor("white")
    ax3.spines[["top", "right"]].set_visible(False)
    ax3.grid(True, color=GRID, linestyle="--", alpha=0.7)
    ax3.set_axisbelow(True)

    ax3.scatter(td_x, td_y, color="#9CA3AF", alpha=0.4, s=30, label="Table Orders (319 items)", zorder=2)
    ax3.plot(x_line, y_line, color=RED, linewidth=2.5, label="Fitted OLS Trend Line", zorder=3)
    ax3.axhline(0, color=INK, linewidth=1.2, linestyle="-")
    ax3.axvline(break_even, color=AMBER, linewidth=1.8, linestyle=":", label=f"Break-Even Discount: {break_even:.1f}%")
    ax3.axvline(26.1, color=RED, linewidth=1.5, linestyle="--", label="Actual Avg Discount: 26.1%")
    ax3.scatter([break_even], [0], color=RED, s=150, zorder=5)

    ax3.set_title(f"Econometric Break-Even Analysis: Tables Turn Negative at {break_even:.1f}% Discount", fontsize=12, pad=12)
    ax3.set_xlabel("Discount Rate (%)", fontsize=10)
    ax3.set_ylabel("Item Profit ($)", fontsize=10)
    ax3.legend(loc="upper right", frameon=True, fontsize=9)
    fig3.tight_layout()
    out3 = FIG / "03_tables_breakeven_regression.png"
    fig3.savefig(out3, dpi=160)
    plt.close(fig3)
    print(f"Generated {out3}")


if __name__ == "__main__":
    generate()
