# E-Commerce Sales & Customer Retention Analytics

## Dự án này là gì?

Dự án biến dữ liệu giao dịch **Online Retail** thành một mô hình **star schema** để phân tích doanh số, hoàn trả và hành vi khách hàng trong Tableau. Dữ liệu gốc có 541.909 dòng, từ **01/12/2010 đến 09/12/2011**. Pipeline giữ nguyên ngày giao dịch, xuất Excel/CSV để kiểm tra, rồi nạp 5 bảng vào SQL Server chạy trong Docker. Đây là dự án phân tích dữ liệu lịch sử, không phải hệ thống bán hàng hay dashboard thời gian thực.

```text
data/raw/data.csv
    ├── notebooks/raw_eda.ipynb          EDA dữ liệu nguồn
    └── src/main.py                      Làm sạch → RFM → star schema
          └── data/processed/             Excel và 5 CSV
                ├── notebooks/ecommerce_analysis.ipynb
                └── src/load_sqlserver.py → SQL Server Docker → Tableau
```

## Dữ liệu và các bảng đầu ra

File nguồn cần các cột `InvoiceNo`, `StockCode`, `Description`, `Quantity`, `InvoiceDate`, `UnitPrice`, `CustomerID`, `Country`. Đặt file tại `data/raw/data.csv`. File nguồn và dữ liệu đã xử lý không được đưa lên Git; người clone dự án cần bổ sung file raw và chạy ETL.

| Bảng | Mỗi dòng đại diện cho | Nội dung chính |
| --- | --- | --- |
| `fact_transactions` | Một dòng hóa đơn mua hoặc hoàn | Mã hóa đơn, thời gian, 4 khóa ngoại, số lượng, giá, gross/return/net sales |
| `dim_date` | Một ngày | Ngày, năm, quý, tháng, ngày trong tháng |
| `dim_customer` | Một khách hàng tại snapshot | CustomerID, Recency, Frequency, Monetary, điểm RFM, value tier, status |
| `dim_product` | Một `StockCode` | Mã và mô tả sản phẩm đại diện |
| `dim_country` | Một quốc gia | Tên quốc gia |

`fact_transactions` nối tới bốn dimension qua `date_key`, `customer_key`, `product_key`, `country_key`. `invoice_no` nằm trong fact vì một hóa đơn có nhiều dòng sản phẩm. `dim_customer` là **ảnh chụp tại một ngày**, nên status/RFM phản ánh tình trạng cuối kỳ, không phải lịch sử thay đổi theo từng tháng.

## ETL xử lý những gì?

1. **Extract:** đọc CSV gốc bằng encoding `ISO-8859-1`, kiểm tra đủ 8 cột cần thiết.
2. **Làm sạch:** parse `InvoiceDate` theo định dạng nguồn; chuyển số lượng, đơn giá, CustomerID sang số; bỏ dòng thiếu các trường thiết yếu, số lượng bằng 0, giá không dương hoặc CustomerID không hợp lệ. **Không dịch ngày.**
3. **Mua và hoàn:** giữ cả `Quantity > 0` và `Quantity < 0`. Tính `gross_sales` từ dòng mua, `return_amount` từ trị tuyệt đối dòng hoàn và `net_sales = gross_sales - return_amount`.
4. **RFM:** snapshot là ngày sau giao dịch cuối cùng. Recency và Frequency chỉ tính từ lần mua; Monetary là net sales sau hoàn. Điểm R/F/M từ 1–5 giữ cùng điểm cho các giá trị bằng nhau. `value_tier` dùng phân vị Monetary 80%; `status` mặc định gắn nhãn không hoạt động nếu quá 180 ngày không mua.
5. **Star schema:** tạo khóa dimension, chọn mô tả xuất hiện nhiều nhất cho mỗi `StockCode`, giữ thời gian đầy đủ và mã hóa đơn ở fact. Pipeline kiểm tra khóa ngoại, số dòng và tổng doanh số trước khi xuất.
6. **Export:** tạo `data/processed/ecommerce_star.xlsx` gồm 5 sheet và 5 CSV cùng tên bảng. Excel để xem, CSV để notebook phân tích và nạp SQL Server.
7. **Load SQL Server:** script riêng tạo database/schema `[ecommerce]`, nạp dimension trước fact trong một transaction, rồi đối chiếu số dòng và tổng net sales. Nếu import lỗi, transaction được rollback.

Các dòng không có CustomerID bị loại khỏi mô hình khách hàng và KPI hiện tại. Các dòng trùng hoàn toàn vẫn được giữ vì nguồn không có mã dòng hóa đơn để xác định chắc chắn đó là lỗi. `status` là **proxy không hoạt động**, chưa phải churn theo cohort. Dữ liệu không có trường tiền tệ, chi phí hay chiến dịch marketing; không suy diễn lợi nhuận hoặc hiệu quả khuyến mãi từ các bảng này.

## Chạy từ đầu

Yêu cầu Python 3.10+, Docker và container SQL Server 2022 có `sqlcmd` tại `/opt/mssql-tools18/bin/sqlcmd`. Các lệnh dưới đây chạy từ thư mục gốc dự án trên macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 1. EDA dữ liệu raw

```bash
python -m jupyter lab
```

Mở [notebooks/raw_eda.ipynb](notebooks/raw_eda.ipynb), chọn kernel `.venv` và **Run All**. Notebook này chỉ đọc `data/raw/data.csv` và có biểu đồ về missing values, giao dịch mua/hoàn, thời gian và quốc gia.

### 2. Chạy ETL và xem Excel

```bash
python src/main.py
```

Mở `data/processed/ecommerce_star.xlsx` để xem 5 sheet. Có thể đổi file nguồn, thư mục xuất hoặc ngưỡng không hoạt động:

```bash
python src/main.py --raw /path/to/data.csv --out /path/to/output --churn-days 180
```

Với file nguồn hiện tại, kết quả kiểm tra là **406.789 dòng fact**, **4.371 khách**, **3.684 sản phẩm**, **37 quốc gia**; gross sales **8.911.407,90**, returns **611.342,09**, net sales **8.300.065,81** (đơn vị tiền theo nguồn).

### 3. Phân tích dữ liệu sau ETL

Mở [notebooks/ecommerce_analysis.ipynb](notebooks/ecommerce_analysis.ipynb) trong JupyterLab và **Run All**. Notebook đọc 5 CSV và có biểu đồ doanh số theo tháng, top thị trường/sản phẩm, trạng thái khách và RFM. Tháng 12/2011 chỉ có dữ liệu đến ngày 09/12; không so sánh trực tiếp với tháng đủ ngày.

### 4. Nạp SQL Server Docker

Container mặc định tên `sql-server` và dùng biến `MSSQL_SA_PASSWORD` **bên trong container**. Script không đọc hoặc ghi mật khẩu vào repo. Kiểm tra container rồi nạp:

```bash
docker ps
python src/load_sqlserver.py
```

Lần đầu script chỉ nạp khi các bảng `[ecommerce]` đang rỗng. Để **thay toàn bộ dữ liệu hiện có** sau khi chạy lại ETL:

```bash
python src/load_sqlserver.py --replace
```

Nếu container có tên khác hoặc ETL xuất sang thư mục khác, thêm `--container TEN_CONTAINER` và `--out /path/to/output`. Script tạo database/schema bằng [sql/star_schema.sql](sql/star_schema.sql), dùng `BULK INSERT` với file tạm trong container, kiểm tra 5 số dòng và net sales trước khi commit. Chạy [sql/analysis.sql](sql/analysis.sql) trong SQL Server để xem các truy vấn mẫu.

### 5. Kết nối Tableau

Chọn connector **Microsoft SQL Server**. Với container hiện tại: server `localhost`, port `1433`, database `ecommerce`, schema `ecommerce`; đăng nhập bằng tài khoản SQL Server của bạn. Thêm `fact_transactions` và bốn dimension vào data source, tạo **Relationships** trên bốn khóa tương ứng. Dùng `net_sales` cho doanh số sau hoàn, hoặc `gross_sales` và `return_amount` nếu cần tách hai phần. Không cộng `monetary_net` từ `dim_customer` sau khi join theo dòng fact vì sẽ nhân giá trị của khách theo số dòng giao dịch.

## Kiểm tra và tài liệu cũ

```bash
python -m unittest discover -s tests -v
```

Dashboard/PDF cũ trong `dashboards/` và `ecommerce_retention_latex_source/` được tạo từ phiên bản từng dịch ngày sang 2024–2025. Chúng chỉ là tham khảo; dashboard Tableau mới cần dùng các bảng SQL Server trong schema `ecommerce`.
