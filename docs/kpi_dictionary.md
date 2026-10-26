# KPI Dictionary: Superstore Sales & Profitability Analytics

Tài liệu định nghĩa chuẩn hóa toàn bộ các chỉ số đo lường hiệu quả kinh doanh (KPI Dictionary) phục vụ đối soát số liệu, xây dựng Data Pipeline SQL và mô hình hóa DAX trong Power BI.

---

## 1. Bảng tra cứu KPI cốt lõi

| Mã KPI | Tên chỉ số | Công thức tính toán | Đơn vị | Grain / Phạm vi tính | Ý nghĩa kinh doanh & Ngưỡng chuẩn |
|:---|:---|:---|:---:|:---|:---|
| **KPI-01** | **Gross Sales** (Doanh thu gộp niêm yết) | `SUM(quantity * list_price)` | USD ($) | Từng dòng đơn hàng (`row_id`) | Giá trị đơn hàng ban đầu theo bảng giá niêm yết trước khi áp dụng chiết khấu thương mại. |
| **KPI-02** | **Net Sales** (Doanh thu ròng thực tế) | `SUM(sales)` = `SUM(quantity * list_price * (1 - discount))` | USD ($) | Từng dòng đơn hàng (`row_id`) | Doanh thu ghi nhận thực tế trên hóa đơn sau khi đã trừ đi giá trị chiết khấu bán hàng. |
| **KPI-03** | **Cost of Goods Sold (COGS)** | `SUM(sales - profit)` | USD ($) | Từng dòng đơn hàng (`row_id`) | Chi phí giá vốn hàng bán, bao gồm giá mua vào và chi phí logistics ước tính trên từng sản phẩm. |
| **KPI-04** | **Net Profit** (Lợi nhuận ròng) | `SUM(profit)` | USD ($) | Từng dòng đơn hàng (`row_id`) | Lợi nhuận thực tế thu về sau khi khấu trừ giá vốn và chiết khấu. Có thể mang giá trị âm nếu bán lỗ. |
| **KPI-05** | **Net Profit Margin %** (Biên lợi nhuận ròng) | `[Net Profit] / [Net Sales] * 100` | % | Toàn công ty / Category / Region | Tỷ suất sinh lời trên mỗi đồng doanh thu. Benchmark chuẩn công ty: **12%–15%**. Ngưỡng cảnh báo: `< 10%`. |
| **KPI-06** | **Average Discount Rate** | `AVERAGE(discount)` hoặc `SUM(sales_undiscounted - sales) / SUM(sales_undiscounted)` | % | Order item / Nhóm sản phẩm | Tỷ lệ giảm giá trung bình cho khách hàng. Ngưỡng an toàn: `< 15%`. Ngưỡng nguy hại (Toxic): `> 20%`. |
| **KPI-07** | **Break-even Discount Rate** | `1 - (COGS / List_Sales)` | % | Từng Sub-Category sản phẩm | Mức chiết khấu tối đa mà tại đó lợi nhuận ròng bằng đúng 0. Vượt quá ngưỡng này, doanh nghiệp sẽ bị âm vốn. |
| **KPI-08** | **Loss-Making Items Share** | `COUNTROWS(FILTER(Fact, profit < 0)) / COUNTROWS(Fact)` | % | Toàn công ty / Sub-Category | Tỷ lệ số dòng đơn hàng bị bán lỗ. Hiện trạng: **18.72%** (1,871 items). Mục tiêu: `< 5%`. |
| **KPI-09** | **Total Dollar Loss Destroyed** | `SUMX(FILTER(Fact, profit < 0), profit)` | USD ($) | Toàn công ty / Khu vực / Quản lý | Tổng số tiền đô la bị thiêu rụi bởi các đơn hàng lỗ. Hiện trạng: **-$156,132 USD**. |
| **KPI-10** | **Return Rate %** (Tỷ lệ hoàn hàng) | `COUNT(DISTINCT returned_orders) / COUNT(DISTINCT total_orders) * 100` | % | Từng bang / Category | Tỷ lệ đơn hàng bị khách trả lại. Benchmark công ty: **8.0%**. Đơn chiết khấu cao kèm hoàn hàng gây lỗ kép. |

---

## 2. Quy tắc phân tầng Chiết khấu (Discount Tiers)

```sql
CASE 
    WHEN discount = 0.00 THEN '0% Full Price'
    WHEN discount > 0.00 AND discount <= 0.10 THEN '1-10% Low Discount'
    WHEN discount > 0.10 AND discount <= 0.20 THEN '11-20% Moderate Discount'
    ELSE '>20% Toxic Discount'
END AS discount_tier
```

| Bậc chiết khấu | Số dòng hàng | Doanh số ròng | Lợi nhuận ròng | Biên lợi nhuận ròng (%) | Trạng thái rủi ro |
|---|:---:|:---:|:---:|:---:|:---|
| **0% Full Price** | 4,798 | $1,087,761 | $325,183 | **+29.9%** | Rất lành mạnh (Động lực lợi nhuận chính) |
| **1-10% Low Discount** | 943 | $334,197 | $80,544 | **+24.1%** | Lành mạnh |
| **11-20% Moderate Discount** | 2,382 | $636,897 | $116,512 | **+18.3%** | Chấp nhận được |
| **>20% Toxic Discount** | 1,871 | $238,346 | -$235,841 | **-38.2%** | **Báo động đỏ: Vực thẳm hủy diệt lợi nhuận** |

---

## 3. Ngưỡng hòa vốn theo danh mục trọng yếu (Break-even Thresholds)

- **Tables (Bàn làm việc):** Ngưỡng hòa vốn là **16.2%**. Mức chiết khấu thực tế đang áp dụng là **26.1%** $\to$ Lỗ ròng -$17,725 USD.
- **Bookcases (Tủ sách):** Ngưỡng hòa vốn là **17.8%**. Mức chiết khấu thực tế đang áp dụng là **21.1%** $\to$ Lỗ ròng -$3,472 USD.
- **Supplies (Văn phòng phẩm):** Ngưỡng hòa vốn là **19.5%**. Mức chiết khấu thực tế đang áp dụng là **22.3%** $\to$ Lỗ ròng -$1,189 USD.
