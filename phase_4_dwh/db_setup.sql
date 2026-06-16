-- ============================================================================
-- FILE: db_setup.sql
-- MỤC TIÊU: Thiết kế Data Warehouse (DWH) theo mô hình hình sao (Star Schema) nâng cấp cho VinFast
-- BỔ SUNG: Phân loại nhóm tác giả (Celebs/KOLs vs Regular Users)
-- HỖ TRỢ: PostgreSQL / MySQL / SQL Server
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. BẢNG CHIỀU THỜI GIAN (Dim_Date)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_date (
    date_key VARCHAR(8) PRIMARY KEY,     -- Định dạng: YYYYMMDD (ví dụ: '20260615')
    full_date DATE NOT NULL,            -- Định dạng ngày chuẩn: YYYY-MM-DD
    day INT NOT NULL,                   -- Ngày (1 - 31)
    month INT NOT NULL,                 -- Tháng (1 - 12)
    year INT NOT NULL,                  -- Năm (ví dụ: 2026)
    quarter INT NOT NULL                -- Quý (1, 2, 3, 4)
);

-- ----------------------------------------------------------------------------
-- 2. BẢNG CHIỀU NGUỒN DỮ LIỆU (Dim_Source)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_source (
    source_key VARCHAR(50) PRIMARY KEY, -- Khóa chính (ví dụ: 'src_youtube', 'src_tinh_te')
    channel_name VARCHAR(100) NOT NULL, -- Tên kênh nguồn (ví dụ: 'Xe Hay', 'Diễn đàn Tinh Tế')
    platform VARCHAR(50) NOT NULL       -- Nền tảng (ví dụ: 'YouTube', 'Forum', 'Facebook')
);

-- ----------------------------------------------------------------------------
-- 3. BẢNG CHIỀU CẢM XÚC (Dim_Sentiment)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_sentiment (
    sentiment_key VARCHAR(50) PRIMARY KEY, -- Định dạng: 'sent_id_...'
    sentiment_label VARCHAR(20) NOT NULL, -- Nhãn cảm xúc: 'Tích cực', 'Tiêu cực', 'Trung lập'
    confidence_score DECIMAL(5,4) NOT NULL -- Điểm tin cậy dự đoán (0.0000 -> 1.0000)
);

-- ----------------------------------------------------------------------------
-- 4. BẢNG CHIỀU DÒNG XE (Dim_Car_Model)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_car_model (
    model_key VARCHAR(50) PRIMARY KEY,     -- Định dạng: 'model_vf3', 'model_byd_atto3'
    model_name VARCHAR(100) NOT NULL,     -- Tên dòng xe: 'VF 3', 'Atto 3', 'Khác/Chung'
    brand VARCHAR(50) NOT NULL,            -- Thương hiệu: 'VinFast', 'BYD', 'Wuling', 'Khác'
    segment VARCHAR(50) NOT NULL           -- Phân khúc: 'A-SUV', 'B-SUV', 'C-SUV', 'Khác'
);

-- Dữ liệu mặc định cho Dim_Car_Model
INSERT IGNORE INTO dim_car_model (model_key, model_name, brand, segment) VALUES 
('model_vf3', 'VF 3', 'VinFast', 'Mini-SUV'),
('model_vf5', 'VF 5', 'VinFast', 'A-SUV'),
('model_vfe34', 'VF e34', 'VinFast', 'C-SUV'),
('model_vf6', 'VF 6', 'VinFast', 'B-SUV'),
('model_vf7', 'VF 7', 'VinFast', 'C-SUV'),
('model_vf8', 'VF 8', 'VinFast', 'D-SUV'),
('model_vf9', 'VF 9', 'VinFast', 'E-SUV'),
('model_byd_atto3', 'Atto 3', 'BYD', 'C-SUV'),
('model_wuling_mini', 'Mini EV', 'Wuling', 'Micro-car'),
('model_xiaomi_su7', 'SU7', 'Xiaomi', 'Sedan'),
('model_other', 'Khác/Chung', 'Khác', 'Khác');

-- ----------------------------------------------------------------------------
-- 5. BẢNG CHIỀU KHÍA CẠNH (Dim_Aspect)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_aspect (
    aspect_key VARCHAR(50) PRIMARY KEY,    -- Định dạng: 'asp_charging', 'asp_software'
    aspect_name VARCHAR(100) NOT NULL,    -- Tên khía cạnh thảo luận
    description TEXT                       -- Mô tả chi tiết khía cạnh
);

-- Dữ liệu mặc định cho Dim_Aspect
INSERT IGNORE INTO dim_aspect (aspect_key, aspect_name, description) VALUES 
('asp_charging', 'Trạm sạc', 'Số lượng, phân bố, tốc độ sạc, sự tiện lợi của hệ thống trạm sạc'),
('asp_battery', 'Pin & Thuê pin', 'Chính sách thuê pin, dung lượng pin, chai pin, sạc tại nhà'),
('asp_software', 'Phần mềm & Lỗi vặt', 'Lỗi phần mềm, treo màn hình, ADAS, lỗi ảo, cập nhật firmware'),
('asp_comfort', 'Vận hành & Tiện nghi', 'Động cơ, cảm giác lái, cách âm, điều hòa, độ êm ái, nội thất'),
('asp_service', 'Dịch vụ & Hậu mãi', 'Chính sách bảo hành, dịch vụ cứu hộ, thái độ showroom, phụ tùng thay thế'),
('asp_price', 'Giá bán & Khuyến mãi', 'Giá xe, chương trình ưu đãi, thuế trước bạ, chi phí vận hành so với xe xăng'),
('asp_other', 'Khác', 'Các chủ đề thảo luận chung hoặc khía cạnh khác không được phân loại');

-- ----------------------------------------------------------------------------
-- 6. BẢNG CHIỀU TÁC GIẢ / NGƯỜI DÙNG (Dim_User)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_user (
    user_key VARCHAR(50) PRIMARY KEY,     -- Định dạng: 'usr_...'
    username VARCHAR(100) NOT NULL,       -- Tên hiển thị người dùng / Kênh KOL
    author_type VARCHAR(20) NOT NULL,     -- Nhóm: 'Celeb' hoặc 'Regular'
    follower_count INT DEFAULT 0          -- Lượng follower / subscribe
);

-- ----------------------------------------------------------------------------
-- 7. BẢNG SỰ KIỆN CHÍNH (Fact_Comments)
-- ----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_comments (
    comment_key VARCHAR(100) PRIMARY KEY,  -- Mã bình luận (ID từ YouTube/Facebook)
    date_key VARCHAR(8) NOT NULL,          -- Khóa ngoại Dim_Date
    source_key VARCHAR(50) NOT NULL,       -- Khóa ngoại Dim_Source
    sentiment_key VARCHAR(50) NOT NULL,    -- Khóa ngoại Dim_Sentiment
    model_key VARCHAR(50) NOT NULL,        -- Khóa ngoại Dim_Car_Model
    aspect_key VARCHAR(50) NOT NULL,       -- Khóa ngoại Dim_Aspect
    user_key VARCHAR(50) NOT NULL,         -- Khóa ngoại Dim_User
    comment_text TEXT NOT NULL,            -- Nội dung bình luận đầy đủ
    like_count INT DEFAULT 0,              -- Số lượt tương tác (Like) bình luận đó

    -- Định nghĩa các Khóa Ngoại (Foreign Keys)
    CONSTRAINT fk_comments_date FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    CONSTRAINT fk_comments_source FOREIGN KEY (source_key) REFERENCES dim_source(source_key),
    CONSTRAINT fk_comments_sentiment FOREIGN KEY (sentiment_key) REFERENCES dim_sentiment(sentiment_key),
    CONSTRAINT fk_comments_model FOREIGN KEY (model_key) REFERENCES dim_car_model(model_key),
    CONSTRAINT fk_comments_aspect FOREIGN KEY (aspect_key) REFERENCES dim_aspect(aspect_key),
    CONSTRAINT fk_comments_user FOREIGN KEY (user_key) REFERENCES dim_user(user_key)
);
