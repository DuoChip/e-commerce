# 🛒 E-Commerce Sales & Customer Retention Analytics
**Project Status:** 🟢 Completed | **Author:** Phạm Đình Được (Đình Đắc)

---

## 📌 Project Overview
Dự án tập trung vào việc phân tích dữ liệu giao dịch (Transactions) và phân đoạn khách hàng (RFM Segmentation) để tối ưu hóa doanh thu và chiến lược giữ chân khách hàng cho doanh nghiệp bán lẻ trực tuyến. 

Dashboard được xây dựng trên **Tableau** nhằm cung cấp cái nhìn toàn diện từ các chỉ số KPI tổng quát đến hành vi chi tiết của từng nhóm khách hàng.

---

## 🎯 Business Objectives
* **Hiệu suất kinh doanh:** Theo dõi các chỉ số quan trọng (Sales, Orders, AOV) theo thời gian thực.
* **Tối ưu hóa tệp khách hàng:** Sử dụng mô hình RFM để nhận diện nhóm khách hàng mang lại giá trị cao (High-Value).
* **Quản trị rủi ro:** Phân tích tỷ lệ khách hàng rời bỏ (Churn Rate) để đề xuất các chiến dịch tái tiếp thị (Re-marketing).

---

## 📂 Dataset Details
Dự án sử dụng hai tập dữ liệu đã qua xử lý (Data Cleaning & Feature Engineering):
1. **`tableau_transactions_final.csv`**: Chứa 13 tháng dữ liệu giao dịch (01/2024 - 01/2025).
   - *Các biến chính:* `InvoiceNo`, `Sales`, `InvoiceDate`, `Quantity`, `UnitPrice`, `CustomerID`, `Country`.
2. **`tableau_rfm_segmentation.csv`**: Kết quả phân loại khách hàng dựa trên điểm số RFM.
   - *Các biến chính:* `Recency`, `Frequency`, `Monetary`, `Status` (Active/Churned), `Is_Top_20`.

---

## 📈 Key KPIs & Visualizations
### 1. Executive Summary (KPI Cards)
* **Total Sales:** Tổng doanh số kèm theo biến động tăng trưởng so với tháng trước (MoM Growth %) và mũi tên chỉ hướng (Arrow Indicator).
* **Total Orders:** Tổng số đơn hàng thành công (được tính bằng `COUNTD` của `InvoiceNo`).
* **Average Order Value (AOV):** Giá trị trung bình của mỗi đơn hàng ($Sales / Invoice$).
* **Churn Rate:** Tỷ lệ phần trăm khách hàng ngừng giao dịch với hệ thống.

### 2. Analytical Charts
* **Sales Trend (Bar/Line Chart):** Theo dõi xu hướng doanh thu theo tháng để nhận diện tính mùa vụ.
* **Customer Status (Donut Chart):** Trực quan hóa tỷ lệ khách hàng Đang hoạt động (Active) vs. Đã rời bỏ (Churned).
* **Top Products & Markets:** Danh sách các sản phẩm bán chạy nhất và thị trường (Country) đóng góp doanh thu lớn nhất.

---

## 🛠 Tech Stack & Techniques
* **Data Processing:** Python (Pandas) - Xử lý dữ liệu thô, gán nhãn trạng thái khách hàng.
* **Visualization:** Tableau Desktop (Public Edition).
* **Analytics:** Time-series Analysis, RFM Scoring, Customer Segmentation.

---

## 🚀 Insights & Actionable Recommendations
* **Insights:** Doanh số có sự bứt phá mạnh mẽ vào quý cuối năm 2024, cho thấy hiệu quả của các chương trình khuyến mãi cuối năm.
* **Recommendations:** Tập trung ngân sách marketing vào nhóm **Top 20% Customers** (High-Value) vì đây là nguồn đóng góp chính vào dòng tiền của doanh nghiệp.

---
## 📬 Contact Information
- **Name:** Phạm Đình Được (Đình Đắc)
- **Position:** Data Analyst Intern Candidate
- **University:** Ho Chi Minh City University of Technology (HCMUT)