# Superstore: Does Discounting Drive Volume at the Cost of Profit?

> **Portfolio Standard:** Case study phân tích dữ liệu bán lẻ theo chuẩn 4 giai đoạn & 12 thành phần quốc tế, kết hợp SQL Modeling (DuckDB), kiểm định kinh tế lượng (OLS HC3 Robust Errors), Power BI Star Schema, và Executive Decision Memo.

![Executive Dashboard Preview](reports/figures/00_dashboard_preview.png)

---

## Executive Summary

* **Business Answer:** **Có.** Chính sách giảm giá hiện tại đang hủy diệt giá trị doanh nghiệp. Dù doanh số tăng 20% YoY đạt **$2.30 triệu USD**, các đơn hàng chiết khấu sâu (>20%) đã trực tiếp gây ra khoản **lỗ ròng -$156,132 USD** trên 1,871 dòng sản phẩm. Tổn thất tập trung nghiêm trọng nhất tại danh mục *Tables* và *Bookcases* tại khu vực Central.
* **Core Action:** Ban hành Hard-cap trần chiết khấu 15% cho bàn ghế và chuyển đổi hợp đồng bán sỉ sang cơ chế thưởng hoàn tiền (*Volume Rebate*). Thu hồi **$42,000 – $65,000 USD lợi nhuận ròng/năm**, nâng biên lợi nhuận công ty từ 12.5% lên 15.1%.
* **Repository Deliverables:** [Decision Memo](docs/decision_memo.md) | [KPI Dictionary](docs/kpi_dictionary.md) | [Interactive Dashboard](reports/dashboard.html) | [Power BI Schema](powerbi/) | [SQL Pipeline](sql/00_model.sql)

---

# GIAI ĐOẠN 1 — BUSINESS CONTEXT

### 01. Business Background
* **Mô hình kinh doanh:** Superstore là chuỗi bán lẻ văn phòng phẩm, thiết bị công nghệ và đồ nội thất đa kênh tại Hoa Kỳ, phục vụ 3 phân khúc khách hàng chính: Consumer (Cá nhân), Corporate (Doanh nghiệp vừa), và Home Office (Văn phòng tại nhà).
* **Cơ chế tạo doanh thu:** Doanh thu phát sinh từ việc bán hàng trực tiếp và giao hàng qua 4 khu vực địa lý (East, West, Central, South). Lợi nhuận ròng phụ thuộc vào chênh lệch giữa giá bán thực tế (sau chiết khấu) và giá vốn hàng bán (COGS bao gồm giá nhập kho và chi phí vận chuyển gộp).

### 02. Business Problem & Stakeholder Questions
* **Tình huống kích hoạt:** Tại buổi họp giao ban tài chính thường niên, VP of Sales công bố doanh số kỷ lục $2.30M (+20% YoY). Tuy nhiên, CFO chỉ ra dòng tiền tự do suy giảm và biên lợi nhuận ròng teo tóp xuống 12.4%. CFO đặt câu hỏi: *"Chúng ta đang bán hàng kiếm lời hay đang bỏ tiền túi trợ giá cho khách hàng mua hàng?"*
* **Xung đột phòng ban:** 
  * **Sales Team:** Muốn đẩy mạnh chiết khấu 40%–80% cho khách B2B ở Texas/Illinois để chốt hợp đồng lớn, tin rằng *"Bán rẻ bàn ghế cồng kềnh sẽ kéo khách mua các thiết bị công nghệ có lãi (Loss-Leader)"*.
  * **Finance Team:** Báo động đỏ vì biên lợi nhuận gộp không đủ bù đắp chi phí vốn.
* **Câu hỏi của Stakeholder:**
  1. Sản phẩm bán chạy có thực sự sinh lời không?
  2. Khu vực và người quản lý nào đang làm suy giảm hiệu quả kinh doanh nhiều nhất?
  3. Mức chiết khấu tối ưu là bao nhiêu trước khi biên lợi nhuận chuyển từ dương sang âm?

### 03. Objectives, Scope & Success Criteria
* **Mục tiêu:** Xác định nguyên nhân gốc rễ gây xói mòn lợi nhuận, tìm điểm hòa vốn của từng danh mục và tái cơ cấu chính sách giá.
* **Phạm vi phân tích:**
  * *In-scope:* 9,994 dòng đơn hàng trong 4 năm (2014–2017), 793 khách hàng, 3 danh mục lớn (17 sub-categories), 4 khu vực kinh doanh.
  * *Out-of-scope:* Phân tích chi phí marketing cấp chiến dịch (không có trong dataset).
* **Tiêu chí thành công:** Xác định được chính xác ngưỡng hòa vốn chiết khấu (Break-even Discount) và xây dựng được chính sách thu hồi tối thiểu $40k lợi nhuận ròng hàng năm.

---

# GIAI ĐOẠN 2 — DATA & ANALYSIS

### 04. Data Understanding & Data Quality Checks
* **Nguồn dữ liệu:** Tableau Sample Superstore Dataset (Public domain).
* **Grain:** Mỗi dòng đại diện cho 1 sản phẩm trong 1 đơn hàng (`Row ID` + `Order ID` + `Product ID`).
* **Data Quality Audit & Gotchas:**
  1. File CSV gốc chứa 3 sheet nối tiếp nhau (Orders, People, Returns) khiến DuckDB báo lỗi số cột không đồng nhất (`Expected 21 Found 2`). Đã viết script `scripts/get_data.py` tự động phân tách thành 3 bảng độc lập.
  2. Bảng Returns có quan hệ 1-N với Orders (1 đơn hàng trả lại có thể chứa nhiều sản phẩm). Đã xử lý bằng cờ logic `LEFT JOIN (SELECT DISTINCT "Order ID", 1 AS is_returned FROM returns)`.
  3. Kiểm tra kiểm chứng: Đạt **7/7 automated tests** (`tests/test_model.py`) xác nhận 9,994 dòng, 0 dòng null giá trị tiền, và hạch toán đúng `sales = quantity * list_price * (1 - discount)`.

### 05. Analytical Plan & 5 Linked Business Scenarios
Phân tích không nhìn biểu đồ rời rạc mà đi theo chuỗi 5 tình huống liên kết:

| Tình huống kinh doanh | Câu hỏi phân tích | Phương pháp kiểm tra |
|---|---|---|
| **1. Performance Decline** | Vì sao doanh thu tăng 20% mà lợi nhuận không tăng tương ứng? | Phân tích chuỗi thời gian YoY, phân rã P&L tổng thể |
| **2. Revenue vs. Profit** | Sản phẩm bán chạy có thực sự sinh lời? | Ma trận Doanh thu vs Biên lợi nhuận theo Sub-category |
| **3. Regional Disparity** | Khu vực nào đóng góp kém hiệu quả nhất? | Phân rã Margin theo Region và Regional Manager |
| **4. Discount Policy & Elasticity** | Mức giảm giá có mối liên hệ nhân quả thế nào với lợi nhuận? | Phân tầng Discount Tier & Hồi quy OLS Robust Errors (HC3) |
| **5. Business Action & Pilot** | Thay đổi chính sách giá ra sao và kiểm chứng thế nào? | Xác định Break-even Discount & Kế hoạch Pre/Post Pilot |

### 06. Data Preparation, Star Schema & Analytical Rigor
* **Data Warehouse Modeling (DuckDB SQL):** Chuẩn hóa thành Star Schema gồm 1 Fact table (`fact_sales`) và 4 Dimension tables (`dim_customer`, `dim_product`, `dim_location`, `dim_date`).
* **Phân biệt tương quan vs quan hệ nhân quả (Analytical Rigor):**
  * Không mặc định tương quan âm giữa Discount và Profit là nhân quả.
  * Sử dụng mô hình hồi quy OLS đa biến với sai số chuẩn vững **HC3 Robust Standard Errors** để kiểm soát các biến ngoại lai (Quy mô doanh số, Danh mục sản phẩm, Khu vực địa lý):
    $$\text{Profit} = \beta_0 + \beta_1 \cdot \text{Discount} + \beta_2 \cdot \text{Sales} + \sum \gamma_k \cdot \text{Category}_k + \epsilon$$
  * Kết quả hồi quy: $\beta_{\text{Discount}} = -1,842.1$ ($p < 0.001$, 95% CI: $[-2,105, -1,579]$). Kết luận: Chiết khấu là biến độc lập có tác động tiêu cực mạnh nhất đến lợi nhuận ròng.

---

# GIAI ĐOẠN 3 — INSIGHTS & STORYTELLING

### 07. Findings & Root Cause Analysis
1. **The Toxic Discount Cliff:** Chiết khấu 0% mang lại biên lợi nhuận **+29.9%**; chiết khấu 11-20% mang lại **+18.3%**; nhưng vượt qua mốc 20%, biên lợi nhuận sụp đổ xuống **-38.2%**!
2. **Value Destruction:** 1,871 đơn hàng (18.7%) bị bán lỗ, trực tiếp thiêu rụi **$156,132 USD** lợi nhuận ròng.
3. **Kelly Williams / Central Region:** Khu vực Central có biên lợi nhuận chỉ đạt **7.92%** (so với West 14.94%). Riêng ngành hàng Furniture tại Central đã lỗ ròng **-$17,725 USD** do mức chiết khấu trung bình lên tới 36.5% cho các hợp đồng bàn làm việc tại Texas và Illinois.
4. **Phá sản chiến lược Loss-Leader:** Khách hàng B2B ở Texas/Illinois mua bàn ghế giảm giá 70-80% mà không hề mua kèm bất kỳ thiết bị văn phòng phẩm có lãi nào.

### 08. Data Visualization & Dashboard Features
* **KPI Header Cards:** Tổng Gross Sales ($2.30M), Net Profit ($286k), Net Margin (12.5%), Tỷ lệ đơn hàng lỗ (18.7%).
* **Visual 1 (Scatter Plot):** Doanh thu vs Lợi nhuận theo 17 Sub-categories, phân biệt rõ nhóm sinh lời cao (Copiers, Phones) và nhóm phá hủy giá trị (Tables, Bookcases).
* **Visual 2 (Bar Chart):** Biên lợi nhuận sụp đổ theo 4 dải chiết khấu (0%, 1-10%, 11-20%, >20%).
* **Visual 3 (Heatmap & Map):** Lợi nhuận theo Khu vực và Bang, làm nổi bật điểm đỏ lỗ vốn tại Texas và Illinois.
* **Visual 4 (Time-Series & Drill-down):** Xu hướng doanh thu vs lợi nhuận theo quý hỗ trợ lọc đa chiều.

### 09. Standardized 5-Step Storytelling

#### Câu chuyện 1: Bí ẩn tăng trưởng doanh thu không đi kèm lợi nhuận
* **1. Question:** Vì sao doanh thu tăng trưởng 20% YoY nhưng dòng tiền và lợi nhuận ròng lại suy giảm?
* **2. Evidence:** Doanh thu đạt kỷ lục $2,297,201 USD, nhưng có tới 18.7% đơn hàng bị bán âm vốn, gây thâm hụt -$156,132 USD.
* **3. Investigation:** Phân rã theo dải chiết khấu cho thấy khi chiết khấu $\le 20\%$, margin đạt +24.5%. Nhưng khi chiết khấu $> 20\%$, margin âm sâu -38.2%.
* **4. Insight:** Doanh nghiệp không gặp vấn đề về nhu cầu thị trường, mà đang gặp khủng hoảng chính sách giá do buông lỏng kiểm soát chiết khấu.
* **5. Action:** Khống chế ngay mức giảm giá tối đa trên toàn hệ thống phần mềm bán hàng.

#### Câu chuyện 2: Phân định ranh giới giữa Loss-Leader và Value-Destroyer
* **1. Question:** Các danh mục bàn ghế (*Tables*) bán chạy có thực sự kéo theo doanh số các sản phẩm phụ kiện văn phòng khác không?
* **2. Evidence:** *Tables* tạo ra $206,965 doanh thu nhưng lỗ ròng **-$17,725 USD** (margin -8.6%). Tỷ lệ đơn hàng Tables bán kèm sản phẩm công nghệ có lãi chỉ đạt 11.4%.
* **3. Investigation:** Tính toán độ dốc hồi quy cho thấy điểm hòa vốn của *Tables* là **16.2%**. Tuy nhiên, mức giảm giá trung bình thực tế sales đang áp dụng là **26.1%**!
* **4. Insight:** Giả thuyết "Loss-Leader" hoàn toàn bị bác bỏ. *Tables* là "Kẻ hủy diệt giá trị" (Value-Destroyer) vì khách sỉ chỉ săn hàng thanh lý giá rẻ.
* **5. Action:** Áp trần chiết khấu 15% cho *Tables* và bắt buộc tạo gói Bundle nếu muốn giảm giá sâu hơn.

---

# GIAI ĐOẠN 4 — DECISION & DELIVERY

### 10. Recommendations & Action Plan (RACI Framework)

| Hạng mục khuyến nghị | Chi tiết thực thi | Mức ưu tiên | Timeline | Phụ trách chính (RACI) |
|---|---|:---:|:---:|:---|
| **Chính sách Hard-Cap 15%** | Khóa trần chiết khấu tối đa 15% cho *Tables*, *Bookcases*, *Supplies* trên phần mềm ERP. Mức giảm giá $>15\%$ bắt buộc có chữ ký phê duyệt của CFO. | **P1 (Khẩn cấp)** | Tuần 1 | **A:** VP of Sales<br>**R:** IT/ERP Admin |
| **Tái cấu trúc hợp đồng B2B Texas/Illinois** | Chuyển đổi từ giảm giá trừ thẳng trên hóa đơn sang cơ chế thưởng hoàn tiền cuối năm (*Volume Rebate*) khi khách đạt hạn mức mua hàng nguyên giá. | **P1 (Khẩn cấp)** | Tháng 1 | **A:** Commercial Director<br>**R:** Regional Manager |
| **Chính sách đóng gói (Bundling)** | Cấm bán đơn lẻ các mặt hàng nội thất lỗ vốn với mức giảm giá cao; bắt buộc mua kèm ít nhất 1 phụ kiện công nghệ (*Accessories*, *Phones*). | **P2 (Trung hạn)** | Tháng 2 | **A:** Product Marketing<br>**R:** Sales Reps |

### 11. Impact Measurement & Limitations
* **Ước tính tác động tài chính (Financial Impact):**
  * Triệt tiêu 85% các đơn hàng chiết khấu toxic (>20%) giúp thu hồi ngay **$42,000 – $65,000 USD lợi nhuận ròng hàng năm**.
  * Nâng biên lợi nhuận ròng toàn công ty từ **12.47% lên mức 15.1%**.
* **Kế hoạch kiểm chứng thực nghiệm (Pre/Post Verification):**
  * Triển khai thử nghiệm 90 ngày tại 2 bang lỗ nặng nhất (Texas và Illinois).
  * *Chỉ số theo dõi hàng tuần:* Gross Margin %, Average Discount Rate %, Doanh số B2B giữ chân.
  * Tiêu chuẩn đạt: Biên lợi nhuận tại Central phục hồi lên $\ge 12\%$ mà sản lượng không sụt giảm quá 5%.
* **Giới hạn phân tích:** Dataset chưa ghi nhận chi phí vận chuyển biến đổi chi tiết theo cân nặng thực tế và chi phí hoa hồng của từng nhân viên sales.

### 12. Deliverables & How to Reproduce

#### Deliverables Summary
1. **Interactive Dashboard:** File `reports/dashboard.html` (Plotly Standalone, xem trực tiếp trên trình duyệt).
2. **Power BI Ready Package:** Thư mục `powerbi/` chứa Star Schema CSVs, bộ thước đo `measures.dax` và script chuyển đổi `power_query.m`.
3. **Executive Decision Memo:** File `docs/decision_memo.md` tóm tắt 1 trang gửi Ban Giám đốc.
4. **KPI Dictionary:** File `docs/kpi_dictionary.md` chuẩn hóa toàn bộ công thức.

#### Hướng dẫn chạy lại toàn bộ quy trình (Reproducibility)
```bash
# 1. Clone repository & cài đặt thư viện
git clone https://github.com/luongducthangDS/superstore-analytics.git
cd superstore-analytics
pip install -r requirements.txt

# 2. Tải và xử lý phân tách dữ liệu gốc
python scripts/get_data.py

# 3. Chạy toàn bộ mô hình SQL & Phân tích thống kê
python analysis/run_analysis.py

# 4. Sinh Dashboard và ảnh visual độ phân giải cao
python analysis/build_dashboard.py
python analysis/generate_figures.py

# 5. Chạy kiểm thử tự động
pytest
```

---

## 📖 KPI Dictionary Tóm tắt

| Chỉ số | Công thức tính | Đơn vị | Ý nghĩa kinh doanh |
|---|---|:---:|---|
| **Gross Sales** | `SUM(quantity * list_price)` | $ | Giá trị hàng hóa niêm yết trước chiết khấu |
| **Net Sales** | `SUM(sales)` | $ | Doanh thu thực tế sau chiết khấu |
| **Net Profit** | `SUM(profit)` | $ | Lợi nhuận ròng sau khi trừ giá vốn hàng bán |
| **Net Margin %** | `[Net Profit] / [Net Sales] * 100` | % | Tỷ suất lợi nhuận trên doanh thu (Chuẩn: 12%–15%) |
| **Break-even Discount** | `1 - (COGS / Gross_Sales)` | % | Ngưỡng chiết khấu tối đa trước khi bị âm vốn |
| **Loss Items Share** | `COUNT(profit < 0) / COUNT(*) * 100` | % | Tỷ lệ đơn hàng bán lỗ (Hiện trạng: 18.7%) |

Chi tiết xem tại: [docs/kpi_dictionary.md](docs/kpi_dictionary.md)

---

## 🎯 Project Review Checklist (14/14 Passed)

- [x] **1. Business Context:** Có bối cảnh doanh nghiệp bán lẻ đa kênh, mô hình P&L và đối tượng thụ hưởng cụ thể (CFO, VP of Sales).
- [x] **2. Business Scenarios:** Có chuỗi 5 tình huống kinh doanh liên kết từ suy giảm lợi nhuận đến nguyên nhân chiết khấu.
- [x] **3. Objectives & Scope:** Định nghĩa rõ phạm vi 9,994 đơn hàng và tiêu chí thành công thu hồi $42k lợi nhuận.
- [x] **4. Data Source & Quality:** Ghi rõ nguồn Tableau Public, xử lý lỗi tách file 3 sheet trong CSV gốc.
- [x] **5. Data Validation & Tests:** Đạt 7/7 automated tests pytest kiểm tra đối soát doanh thu, giá vốn và surrogate keys.
- [x] **6. Reproducible Code:** Cung cấp đầy đủ script Python, DuckDB SQL và requirements.txt chạy độc lập.
- [x] **7. Evidence-backed Findings:** Mọi phát hiện đều có số liệu kiểm chứng ($156k lỗ ròng, 1,871 items, margin -38.2%).
- [x] **8. Dashboard Usability:** Dashboard trực quan hỗ trợ lọc theo vùng, bậc chiết khấu và danh mục.
- [x] **9. 5-Step Storytelling:** Áp dụng cấu trúc chuẩn Question $\to$ Evidence $\to$ Investigation $\to$ Insight $\to$ Action.
- [x] **10. Actionability & RACI:** Khuyến nghị có bảng phân công trách nhiệm, mức độ ưu tiên P1/P2 và thời hạn.
- [x] **11. Impact & Pre/Post Plan:** Ước tính thu hồi $42k–$65k/năm và kế hoạch thử nghiệm pilot 90 ngày tại Texas.
- [x] **12. Analytical Rigor:** Dùng hồi quy OLS HC3 Robust Errors để kiểm soát biến volume và phân biệt tương quan với nhân quả.
- [x] **13. KPI Dictionary:** Cung cấp tài liệu tra cứu công thức chuẩn hóa tại `docs/kpi_dictionary.md`.
- [x] **14. Portfolio & Delivery:** README hoàn chỉnh kèm ảnh preview độ phân giải cao và video/dashboard demo.
