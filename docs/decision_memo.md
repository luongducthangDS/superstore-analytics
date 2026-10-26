# Decision Memo: Eliminating the $156k Margin Drain from Toxic Discounts

**To:** Leadership Team & VP of Sales  
**From:** Data Analyst  
**Date:** October 2026  
**Subject:** Root-cause analysis of Superstore discount elasticity and regional margin erosion  

---

## Executive Summary
Despite delivering **$2.30M in top-line revenue**, Superstore suffered **$156,132 in net losses** across 1,871 order items (18.7% of all items sold). The root cause is not low product demand or shipping costs, but an uncontrolled discounting policy: when discounts exceed 20%, average order profitability plunges from **+28.5% margin down to -38.2%**.

In the Central region under regional manager Kelly Williams, Furniture discounts averaged 36.5%, driving a net loss of **-$17,725** and dragging Central's profit margin down to **7.9%** (vs. 14.9% in the West).

---

## Key Quantitative Evidence

| Finding | Metric |
| :--- | :--- |
| **Gross Sales & Net Profit** | **$2,297,201** Sales $\to$ **$286,398** Net Profit (12.5% overall margin) |
| **Loss-Making Items** | **1,871 items (18.7%)**, causing **-$156,132** in total value destruction |
| **The Toxic Discount Cliff** | 0% discount: **+29.9% margin** \| 1–10%: **+24.1%** \| 11–20%: **+18.3%** \| **>20%: -38.2% margin** |
| **Break-even Discount** | Tables break even at **16.2% discount**; Bookcases break even at **17.8% discount** |
| **Central Region Drain** | Central delivered **$501k in sales** but only **$39.7k profit (7.9%)**, due to 80% discount on B2B office tables in Texas and Illinois |
| **Regression with HC3 Errors** | $\beta_{\text{discount}} = -1,842.1$ ($p < 0.001$), confirming discounting is the primary controllable driver of margin loss after controlling for volume and category |

---

## Action Plan & Financial Impact

1. **Immediate Hard Cap on Discounting (Day 1):**
   - Implement an automated system hard-cap at **15% maximum discount** for *Tables*, *Bookcases*, and *Supplies*.
   - Any discount exceeding 15% requires written sign-off from the VP of Sales.
2. **Restructure Central Region Commercial Terms (Month 1):**
   - End blanket promotional allowances in Texas and Illinois. Transition wholesale buyers to volume rebates rather than front-end price cuts.
3. **Product Bundling Strategy (Quarter 1):**
   - Require high-loss furniture items to be bundled with high-margin technology/accessories (Phones/Accessories averaging +54% margin) to preserve basket profitability.

**Estimated Financial Impact:**  
Eliminating toxic discounts on the bottom 3 sub-categories recovers **$42,000 to $65,000 annually in net bottom-line profit**, increasing total corporate net margin from **12.5% to 15.1%**.
