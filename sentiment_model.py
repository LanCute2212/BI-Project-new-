import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
from preprocess import preprocess_vietnamese_text

# Đường dẫn file dữ liệu
RAW_DATA_CANDIDATES = [
    "rawdata.csv",
    os.path.join("data", "raw_comments.csv"),
    os.path.join("data", "rawdata.csv"),
]
PROCESSED_DATA_PATH = os.path.join("data", "processed_comments.csv")
DB_PATH = os.path.join("data", "sentiment_dwh.db")


def resolve_raw_data_path():
    for candidate in RAW_DATA_CANDIDATES:
        if os.path.exists(candidate):
            return candidate
    return RAW_DATA_CANDIDATES[0]

# Danh sách từ vựng hỗ trợ cho mô hình Lexicon dự phòng (khi không có Internet/PyTorch)
POSITIVE_KEYWORDS = ["đẹp", "tốt", "êm", "rẻ", "thích", "sướng", "tiết kiệm", "hợp lý", "ngon", "yêu", "đỉnh", "tiện", "cute", "đầm"]
NEGATIVE_KEYWORDS = ["lỗi", "chán", "kém", "đắt", "tệ", "hỏng", "bất tiện", "chậm", "ít", "mệt", "yếu", "lỏng lẻo", "hoang mang"]

def run_phobert_sentiment(texts):
    """
    Sử dụng mô hình PhoBERT đã được train sẵn để dự đoán cảm xúc (Positive, Negative, Neutral).
    Nếu gặp lỗi (thiếu thư viện, không có GPU/Internet), hệ thống sẽ tự động chuyển sang Lexicon Fallback.
    """
    print("[*] Đang tải mô hình PhoBERT (w11wo/phobert-base-vietnamese-sentiment) từ Hugging Face...")
    try:
        from transformers import pipeline
        # Khởi tạo pipeline phân tích cảm xúc
        # w11wo/phobert-base-vietnamese-sentiment trả về nhãn:
        # Label 0: Negative, Label 1: Neutral, Label 2: Positive (hoặc tương tự tùy model mapping)
        classifier = pipeline(
            "sentiment-analysis", 
            model="w11wo/phobert-base-vietnamese-sentiment",
            tokenizer="w11wo/phobert-base-vietnamese-sentiment"
        )
        
        results = []
        for i, text in enumerate(texts):
            # Tokenize câu trước khi đưa vào PhoBERT (yêu cầu tách từ)
            segmented_text = preprocess_vietnamese_text(text, tokenize=True)
            # Giới hạn chiều dài chuỗi đầu vào (PhoBERT hỗ trợ tối đa 256/512 tokens)
            truncated_text = " ".join(segmented_text.split()[:150])
            
            if not truncated_text.strip():
                results.append(("Trung lập", 0.5))
                continue
                
            prediction = classifier(truncated_text)[0]
            label = prediction['label']
            score = prediction['score']
            
            # Map nhãn đầu ra sang tiếng Việt
            # Model w11wo trả về nhãn như '0', '1', '2' hoặc 'NEG', 'NEU', 'POS'
            label_map = {
                '0': 'Tiêu cực', '1': 'Trung lập', '2': 'Tích cực',
                'NEG': 'Tiêu cực', 'NEU': 'Trung lập', 'POS': 'Tích cực',
                'negative': 'Tiêu cực', 'neutral': 'Trung lập', 'positive': 'Tích cực',
                'LABEL_0': 'Tiêu cực', 'LABEL_1': 'Trung lập', 'LABEL_2': 'Tích cực'
            }
            sentiment = label_map.get(label.upper(), "Trung lập")
            results.append((sentiment, score))
            
            if (i+1) % 10 == 0:
                print(f"    - Đã xử lý {i+1}/{len(texts)} dòng...")
                
        return results

    except Exception as e:
        print(f"[!] Cảnh báo: Không thể tải mô hình PhoBERT trực tuyến ({e}).")
        print("[!] Tự động chuyển sang thuật toán Lexicon thay thế cho môi trường thử nghiệm...")
        
        # Hàm dự phòng Lexicon rule-based
        results = []
        for text in texts:
            cleaned = preprocess_vietnamese_text(text, tokenize=False)
            pos_count = sum(1 for word in POSITIVE_KEYWORDS if word in cleaned)
            neg_count = sum(1 for word in NEGATIVE_KEYWORDS if word in cleaned)
            
            if pos_count > neg_count:
                results.append(("Tích cực", 0.7 + (pos_count * 0.05)))
            elif neg_count > pos_count:
                results.append(("Tiêu cực", 0.7 + (neg_count * 0.05)))
            else:
                results.append(("Trung lập", 0.5))
        return results

def setup_sqlite_database():
    """
    Khởi tạo database SQLite đại diện cho Data Warehouse (mô hình Star Schema).
    """
    print(f"[*] Đang khởi tạo Database Data Warehouse tại: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Tạo bảng chiều Dim_Date
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_date (
        date_key TEXT PRIMARY KEY,
        full_date TEXT,
        day INTEGER,
        month INTEGER,
        year INTEGER,
        quarter INTEGER
    )
    """)
    
    # 2. Tạo bảng chiều Dim_Source
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_source (
        source_key TEXT PRIMARY KEY,
        channel_name TEXT,
        platform TEXT
    )
    """)
    
    # 3. Tạo bảng chiều Dim_Sentiment
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS dim_sentiment (
        sentiment_key TEXT PRIMARY KEY,
        sentiment_label TEXT,
        confidence_score REAL
    )
    """)
    
    # 4. Tạo bảng sự kiện Fact_Comments
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fact_comments (
        comment_key TEXT PRIMARY KEY,
        date_key TEXT,
        source_key TEXT,
        sentiment_key TEXT,
        author TEXT,
        comment_text TEXT,
        like_count INTEGER,
        FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
        FOREIGN KEY (source_key) REFERENCES dim_source(source_key),
        FOREIGN KEY (sentiment_key) REFERENCES dim_sentiment(sentiment_key)
    )
    """)
    
    conn.commit()
    conn.close()
    print("[+] Khởi tạo Database thành công!")

def load_data_to_dwh(df):
    """
    Nạp dữ liệu từ DataFrame đã phân tích cảm xúc vào Data Warehouse SQLite.
    """
    print("[*] Đang thực hiện ETL: Load dữ liệu vào Data Warehouse...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Xóa dữ liệu cũ để tránh trùng lặp khi chạy lại demo
    cursor.execute("DELETE FROM fact_comments")
    cursor.execute("DELETE FROM dim_date")
    cursor.execute("DELETE FROM dim_source")
    cursor.execute("DELETE FROM dim_sentiment")
    
    for index, row in df.iterrows():
        # 1. Trích xuất thời gian để nạp vào Dim_Date
        try:
            dt = datetime.strptime(row['published_at'], "%Y-%m-%dT%H:%M:%SZ")
        except:
            dt = datetime.now()
            
        date_key = dt.strftime("%Y%m%d")
        full_date = dt.strftime("%Y-%m-%d")
        quarter = (dt.month - 1) // 3 + 1
        
        cursor.execute("""
        INSERT OR IGNORE INTO dim_date (date_key, full_date, day, month, year, quarter)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (date_key, full_date, dt.day, dt.month, dt.year, quarter))
        
        # 2. Nạp dữ liệu vào Dim_Source
        source_name = row['source']
        source_key = "src_" + source_name.lower().replace(" ", "_")
        cursor.execute("""
        INSERT OR IGNORE INTO dim_source (source_key, channel_name, platform)
        VALUES (?, ?, ?)
        """, (source_key, source_name, "Social Media"))
        
        # 3. Nạp dữ liệu vào Dim_Sentiment
        sentiment_key = f"sent_{index}"
        cursor.execute("""
        INSERT OR IGNORE INTO dim_sentiment (sentiment_key, sentiment_label, confidence_score)
        VALUES (?, ?, ?)
        """, (sentiment_key, row['sentiment'], float(row['sentiment_score'])))
        
        # 4. Nạp dữ liệu vào Fact_Comments
        cursor.execute("""
        INSERT INTO fact_comments (comment_key, date_key, source_key, sentiment_key, author, comment_text, like_count)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            row['comment_id'],
            date_key,
            source_key,
            sentiment_key,
            row['author'],
            row['comment_text'],
            int(row['like_count'])
        ))
        
    conn.commit()
    conn.close()
    print("[+] Hoàn thành ETL! Dữ liệu đã sẵn sàng cho Dashboard.")

if __name__ == "__main__":
    # Đảm bảo có dữ liệu thô đầu vào
    raw_data_path = resolve_raw_data_path()
    if not os.path.exists(raw_data_path):
        print(f"[!] Không tìm thấy file {raw_data_path}. Đang chạy crawler để tạo dữ liệu...")
        import subprocess
        subprocess.run(["python", "crawler.py"])
        raw_data_path = resolve_raw_data_path()

    # Đọc dữ liệu
    df = pd.read_csv(raw_data_path)
    
    # Chạy mô hình Sentiment Analysis
    texts = df['comment_text'].tolist()
    sentiment_results = run_phobert_sentiment(texts)
    
    # Lưu kết quả phân tích vào dataframe
    df['sentiment'] = [res[0] for res in sentiment_results]
    df['sentiment_score'] = [res[1] for res in sentiment_results]
    
    # Xuất file CSV đã gán nhãn
    df.to_csv(PROCESSED_DATA_PATH, index=False, encoding="utf-8-sig")
    print(f"[+] Đã lưu dữ liệu đã gán nhãn cảm xúc tại: {PROCESSED_DATA_PATH}")
    
    # Cài đặt CSDL và nạp dữ liệu
    setup_sqlite_database()
    load_data_to_dwh(df)
