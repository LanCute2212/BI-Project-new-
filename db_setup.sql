-- ============================================================================
-- FILE: db_setup.sql
-- MỤC TIÊU: Thiết kế Data Warehouse (DWH) theo mô hình hình sao (Star Schema)
-- HỖ TRỢ: PostgreSQL / MySQL / SQL Server
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. BẢNG CHIỀU THỜI GIAN (Dim_Date)
-- ----------------------------------------------------------------------------
CREATE TABLE dim_date (
    date_key VARCHAR(8) PRIMARY KEY,     -- Định dạng: YYYYMMDD (ví dụ: '20260615')
    full_date DATE NOT NULL,            -- Định dạng ngày chuẩn: YYYY-MM-DD
    day INT NOT NULL,                   -- Ngày (1 - 31)
    month INT NOT NULL,                 -- Tháng (1 - 12)
    year INT NOT NULL,                  -- Năm (ví dụ: 2026)
    quarter INT NOT NULL                -- Quý (1, 2, 3, 4)
);

-- Dữ liệu mẫu cho bảng Dim_Date (nếu cần dùng SQL chay)
-- INSERT INTO dim_date (date_key, full_date, day, month, year, quarter) VALUES ('20260615', '2026-06-15', 15, 6, 2026, 2);

-- ----------------------------------------------------------------------------
-- 2. BẢNG CHIỀU NGUỒN DỮ LIỆU (Dim_Source)
-- ----------------------------------------------------------------------------
CREATE TABLE dim_source (
    source_key VARCHAR(50) PRIMARY KEY, -- Khóa chính (ví dụ: 'src_youtube', 'src_tinh_te')
    channel_name VARCHAR(100) NOT NULL, -- Tên kênh nguồn (ví dụ: 'Xe Hay', 'Diễn đàn Tinh Tế')
    platform VARCHAR(50) NOT NULL       -- Nền tảng (ví dụ: 'YouTube', 'Forum', 'Facebook')
);

-- Dữ liệu mặc định cho Dim_Source
INSERT INTO dim_source (source_key, channel_name, platform) VALUES 
('src_youtube', 'YouTube Channel', 'YouTube'),
('src_tinh_te', 'Diễn đàn Tinh Tế', 'Forum'),
('src_facebook_group', 'Cộng Đồng Xe Điện Việt', 'Facebook');

-- ----------------------------------------------------------------------------
-- 3. BẢNG CHIỀU CẢM XÚC (Dim_Sentiment)
-- ----------------------------------------------------------------------------
CREATE TABLE dim_sentiment (
    sentiment_key VARCHAR(50) PRIMARY KEY, -- Định dạng: 'sent_id_...'
    sentiment_label VARCHAR(20) NOT NULL, -- Nhãn cảm xúc: 'Tích cực', 'Tiêu cực', 'Trung lập'
    confidence_score DECIMAL(5,4) NOT NULL -- Điểm tin cậy dự đoán (0.0000 -> 1.0000)
);

-- ----------------------------------------------------------------------------
-- 4. BẢNG SỰ KIỆN CHÍNH (Fact_Comments)
-- ----------------------------------------------------------------------------
CREATE TABLE fact_comments (
    comment_key VARCHAR(100) PRIMARY KEY,  -- Mã bình luận (ID từ YouTube/Facebook)
    date_key VARCHAR(8) NOT NULL,          -- Khóa ngoại Dim_Date
    source_key VARCHAR(50) NOT NULL,       -- Khóa ngoại Dim_Source
    sentiment_key VARCHAR(50) NOT NULL,    -- Khóa ngoại Dim_Sentiment
    author VARCHAR(100),                   -- Tên người viết bình luận
    comment_text TEXT NOT NULL,            -- Nội dung bình luận đầy đủ
    like_count INT DEFAULT 0,              -- Số lượt tương tác (Like) bình luận đó

    -- Định nghĩa các Khóa Ngoại (Foreign Keys)
    CONSTRAINT fk_comments_date FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
    CONSTRAINT fk_comments_source FOREIGN KEY (source_key) REFERENCES dim_source(source_key),
    CONSTRAINT fk_comments_sentiment FOREIGN KEY (sentiment_key) REFERENCES dim_sentiment(sentiment_key)
);

-- ----------------------------------------------------------------------------
-- MỘT SỐ CÂU TRUY VẤN INSIGHT DỰ PHÒNG (Dành cho việc kiểm tra)
-- ----------------------------------------------------------------------------
-- 1. Thống kê tỷ lệ cảm xúc trong kho dữ liệu:
-- SELECT ds.sentiment_label, COUNT(f.comment_key) AS Total, SUM(f.like_count) AS Total_Likes
-- FROM fact_comments f
-- JOIN dim_sentiment ds ON f.sentiment_key = ds.sentiment_key
-- GROUP BY ds.sentiment_label;

-- 2. Xem xu hướng thảo luận theo tháng/quý:
-- SELECT dd.year, dd.month, ds.sentiment_label, COUNT(f.comment_key) AS Comments
-- FROM fact_comments f
-- JOIN dim_date dd ON f.date_key = dd.date_key
-- JOIN dim_sentiment ds ON f.sentiment_key = ds.sentiment_key
-- GROUP BY dd.year, dd.month, ds.sentiment_label
-- ORDER BY dd.year, dd.month;
