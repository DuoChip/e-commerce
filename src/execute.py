import pandas as pd
import numpy as np
import datetime as dt
import os

# ==========================================
# BULLET 1 (CV): CLEANED & PRE-PROCESSED 10,000+ RECORDS
# ==========================================
print("1. Đang tải và làm sạch dữ liệu (Data Cleaning)...")

# Xác định đường dẫn thư mục gốc
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_DATA_PATH = os.path.join(BASE_DIR, 'data', 'raw', 'data.csv')

# --- MOCK DATA (10,000+ records như trong CV) ---
np.random.seed(42)
mock_data = {
    'InvoiceNo': np.random.randint(536000, 537000, 10500),
    'StockCode': ['85123A'] * 10500,
    'Quantity': np.random.randint(-5, 20, 10500), # Chứa inconsistent format (số âm do hoàn trả)
    'InvoiceDate': pd.date_range(start='2024-01-01', end='2024-12-31', periods=10500),
    'UnitPrice': np.random.uniform(1.0, 50.0, 10500),
    'CustomerID': np.random.choice([np.nan, 17850, 14688, 15311, 13047, 18074, 12583, 19000, 19001, 19002], 10500) # Chứa missing values
}
df = pd.DataFrame(mock_data)
# ---------------------------------------------------------

print(f"-> Số dòng ban đầu: {len(df)}")

# Xử lý Missing Values: Xóa các dòng không định danh được khách hàng
df_clean = df.dropna(subset=['CustomerID'])

# Xử lý Inconsistent Formats: Loại bỏ các đơn hàng có Quantity <= 0 (đơn lỗi/hoàn trả)
df_clean = df_clean[df_clean['Quantity'] > 0]

# Tính doanh thu từng dòng giao dịch
df_clean['Sales'] = df_clean['Quantity'] * df_clean['UnitPrice']

print(f"-> Số dòng sau khi làm sạch: {len(df_clean)}")

# ==========================================
# BULLET 2 & 3 (CV): RFM ANALYSIS, LTV, CHURN & TOP 20%
# ==========================================
print("\n2. Đang phân tích RFM và LTV...")

df_clean['InvoiceDate'] = pd.to_datetime(df_clean['InvoiceDate'])
# Lấy ngày hiện tại làm mốc (Snapshot date)
snapshot_date = df_clean['InvoiceDate'].max() + dt.timedelta(days=1)

# Tính RFM cho từng khách hàng
rfm = df_clean.groupby('CustomerID').agg({
    'InvoiceDate': lambda x: (snapshot_date - x.max()).days, # Recency: Số ngày từ lần mua cuối
    'InvoiceNo': 'nunique',                                  # Frequency: Số đơn hàng
    'Sales': 'sum'                                           # Monetary: Tổng chi tiêu (Historical LTV)
}).reset_index()

rfm.rename(columns={
    'InvoiceDate': 'Recency',
    'InvoiceNo': 'Frequency',
    'Sales': 'Monetary'
}, inplace=True)

# Tính Customer LTV (Historical Lifetime Value) và AOV (Average Order Value)
rfm['Customer_LTV'] = rfm['Monetary']
rfm['Average_Order_Value'] = rfm['Monetary'] / rfm['Frequency']

print("3. Tính toán Churn Rate & Customer Segmentation (Top 20%)...")

# Định nghĩa Churn (Khách hàng rời bỏ): Không mua hàng trong 6 tháng (180 ngày) qua
rfm['Is_Churned'] = np.where(rfm['Recency'] > 180, 1, 0)

# Phân khúc khách hàng: Tìm Top 20% High-Value Clients dựa trên Customer LTV (Monetary)
# Lấy mốc bách phân vị thứ 80 (80th percentile)
top_20_threshold = rfm['Customer_LTV'].quantile(0.80)

# Gắn nhãn phân khúc
rfm['Segment'] = np.where(
    rfm['Customer_LTV'] >= top_20_threshold, 
    'Top 20% High-Value', 
    'Standard Client'
)

# ==========================================
# XUẤT DỮ LIỆU CHO TABLEAU DASHBOARD
# ==========================================
print("\n4. Đang xuất file dữ liệu cho Tableau...")

# Bảng 1: Bảng tổng hợp RFM & Segmentation (Dùng để vẽ biểu đồ khách hàng)
PROCESSED_RFM_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'tableau_rfm_segmentation.csv')
os.makedirs(os.path.dirname(PROCESSED_RFM_PATH), exist_ok=True)
rfm.to_csv(PROCESSED_RFM_PATH, index=False)

# Bảng 2: Bảng chi tiết giao dịch đã làm sạch (Dùng để vẽ Time-series Sales trên Tableau)
# Gắn thêm nhãn Segment vào từng dòng giao dịch để Tableau dễ filter
df_final = df_clean.merge(rfm[['CustomerID', 'Segment', 'Is_Churned']], on='CustomerID', how='left')
PROCESSED_TRANSACTIONS_PATH = os.path.join(BASE_DIR, 'data', 'processed', 'tableau_transactions_clean.csv')
df_final.to_csv(PROCESSED_TRANSACTIONS_PATH, index=False)

print(f"-> Đã xuất file tổng hợp khách hàng: {PROCESSED_RFM_PATH}")
print(f"-> Đã xuất file chi tiết giao dịch: {PROCESSED_TRANSACTIONS_PATH}")
print("\nHOÀN TẤT! Bạn có thể import 2 file CSV này vào Tableau để xây dựng Dashboard.")