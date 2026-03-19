# 1. Tạo thư mục tổng và di chuyển vào trong
mkdir e-commerce
cd e-commerce

# 2. Khởi tạo Git (nếu chưa có)
git init

# 3. Tạo các thư mục con
mkdir data notebooks src models dashboards

# 4. Tạo các file .gitkeep để Git không bỏ qua thư mục rỗng
touch data/.gitkeep
touch notebooks/.gitkeep
touch src/.gitkeep
touch models/.gitkeep
touch dashboards/.gitkeep

# 5. Lưu lại thay đổi trên local
git add .
git commit -m "Init project structure for e-commerce churn prediction"