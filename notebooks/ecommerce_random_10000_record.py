# %% [markdown]
# # Phân tích Khám phá Dữ liệu (EDA) - E-commerce Sales
# File Notebook này đóng vai trò là "bản nháp" để khám phá dữ liệu thô, 
# phát hiện các vấn đề (Missing Values, Inconsistent Formats) trước khi 
# đưa vào pipeline xử lý tự động.

# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os

# %% [markdown]
# ## 1. Load Dữ liệu Thô
# Giả sử file dữ liệu gốc nằm ở thư mục data/raw/
# %%
# Xác định đường dẫn (điều chỉnh tùy theo vị trí bạn mở Jupyter Notebook)
raw_data_path = '../data/raw/data.csv'
df = pd.read_csv(raw_data_path, encoding='ISO-8859-1')

# Tạm thời dùng Mock Data giống Pipeline để demo trong Notebook này
import numpy as np
np.random.seed(42)
df = pd.DataFrame({
    'InvoiceNo': np.random.randint(536000, 537000, 10500),
    'StockCode': ['85123A'] * 10500,
    'Quantity': np.random.randint(-5, 20, 10500), 
    'InvoiceDate': pd.date_range(start='2024-01-01', end='2024-12-31', periods=10500),
    'UnitPrice': np.random.uniform(1.0, 50.0, 10500),
    'CustomerID': np.random.choice([np.nan, 17850, 14688, 15311, 13047, 18074], 10500)
})

print("Kích thước dữ liệu thô:", df.shape)
df.head()

# %% [markdown]
# ## 2. Phát hiện Missing Values
# Đây là minh chứng cho việc bạn đã "handle missing values" như trong CV.
# %%
# Kiểm tra tổng số lượng missing values ở từng cột
print("Số lượng Missing Values theo cột:")
print(df.isnull().sum())

# Tính phần trăm Missing của CustomerID
missing_pct = df['CustomerID'].isnull().sum() / len(df) * 100
print(f"\n=> Tỷ lệ đơn hàng không có CustomerID: {missing_pct:.2f}%")
print("=> Quyết định: Sẽ drop các dòng thiếu CustomerID trong Pipeline vì không thể tính RFM.")

# %% [markdown]
# ## 3. Phát hiện Inconsistent Formats (Dữ liệu lỗi/phi lý)
# Khám phá các cột số học (Quantity, UnitPrice) xem có giá trị âm hay không.
# %%
df.describe()

# %%
# Vẽ biểu đồ phân phối của Quantity để trực quan hóa lỗi
plt.figure(figsize=(8, 4))
sns.boxplot(x=df['Quantity'])
plt.title('Phân phối số lượng sản phẩm trên mỗi đơn hàng (Quantity)')
plt.axvline(x=0, color='r', linestyle='--')
plt.show()

# %%
negative_qty = len(df[df['Quantity'] <= 0])
print(f"Số lượng đơn hàng có Quantity <= 0 (Bị hủy/hoàn trả): {negative_qty} dòng")
print("=> Quyết định: Sẽ filter loại bỏ các dòng Quantity <= 0 trong Pipeline.")

# %% [markdown]
# ## 4. Phân tích Sơ bộ Về Doanh thu (Sales)
# %%
# Thử tính doanh thu sau khi drop lỗi
df_clean = df.dropna(subset=['CustomerID'])
df_clean = df_clean[df_clean['Quantity'] > 0]
df_clean['Sales'] = df_clean['Quantity'] * df_clean['UnitPrice']

print("Top 5 khách hàng chi tiêu nhiều nhất (Historical LTV sơ bộ):")
print(df_clean.groupby('CustomerID')['Sales'].sum().sort_values(ascending=False).head())

# %% [markdown]
# ### Kết luận từ EDA:
# 1. Tập dữ liệu có khoảng ~16% missing values ở cột `CustomerID`. Cần drop.
# 2. Cột `Quantity` có chứa giá trị âm, đại diện cho các đơn hàng bị hủy. Cần drop.
# 
# -> Đã có đủ thông tin và logic để viết script tự động hóa `src/rfm_churn_pipeline.py`.
# %%
