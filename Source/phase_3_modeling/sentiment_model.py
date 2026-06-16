import os
import sys
import pandas as pd
import numpy as np
import codecs
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
if "phase_" in os.path.basename(current_dir).lower() or "phase_" in current_dir.lower():
    BASE_DIR = os.path.abspath(os.path.join(current_dir, ".."))
else:
    BASE_DIR = current_dir

sys.path.append(os.path.join(BASE_DIR, "phase_2_preprocess"))
from preprocess import preprocess_vietnamese_text

MYSQL_HOST = "localhost"
MYSQL_PORT = 3306
MYSQL_USER = "root"
MYSQL_PASSWORD = "" 
MYSQL_DATABASE = "sentiment_dwh"

if sys.platform.startswith('win'):
    if hasattr(sys.stdout, 'buffer'):
        try:
            sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'replace')
        except Exception:
            pass
    if hasattr(sys.stderr, 'buffer'):
        try:
            sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'replace')
        except Exception:
            pass

RAW_DATA_PATH = os.path.join(BASE_DIR, "data", "raw_comments.csv")
PROCESSED_DATA_PATH = os.path.join(BASE_DIR, "data", "processed_comments.csv")
DB_PATH = os.path.join(BASE_DIR, "data", "sentiment_dwh.db")

POSITIVE_KEYWORDS = [
    "đẹp", "tốt", "êm", "rẻ", "thích", "sướng", "tiết kiệm", "hợp lý", "ngon", "yêu", "đỉnh", 
    "tiện", "cute", "đầm", "mượt", "tiện_lợi", "hài_lòng", "đầm_chắc", "cách_âm_tốt", "rộng_rãi", 
    "bốc", "vượt_trội", "nhanh", "chu_đáo", "yên_tâm", "chuyên_nghiệp", "tiện_ích"
]
NEGATIVE_KEYWORDS = [
    "lỗi", "chán", "kém", "đắt", "tệ", "hỏng", "bất_tiện", "chậm", "ít", "mệt", "yếu", 
    "lỏng_lẻo", "hoang_mang", "dở", "kém_chất_lượng", "lỗi_ảo", "hao_pin", "chờ_lâu", "ồn", 
    "xóc", "quá_tải", "khan_hiếm", "rớt_giá", "cứng", "lỏng_lẻo", "cót_kẹt"
]
NEGATION_WORDS = ["không", "chưa", "chẳng", "chả", "không_được"]
INTENSIFIER_WORDS = ["rất", "quá", "lắm", "cực_kỳ", "vô_cùng", "hoàn_toàn", "khá", "cực"]

CAR_MODEL_KEYWORDS = {
    "model_vf3": ["vf3", "vf 3"],
    "model_vf5": ["vf5", "vf 5"],
    "model_vfe34": ["vfe34", "vf e34", "e34"],
    "model_vf6": ["vf6", "vf 6"],
    "model_vf7": ["vf7", "vf 7"],
    "model_vf8": ["vf8", "vf 8"],
    "model_vf9": ["vf9", "vf 9"],
    "model_byd_atto3": ["atto 3", "atto3", "byd"],
    "model_wuling_mini": ["wuling", "mini ev", "miniev"],
    "model_xiaomi_su7": ["xiaomi", "su7"]
}

ASPECT_KEYWORDS = {
    "asp_charging": ["sạc", "trạm sạc", "cổng sạc", "sạc nhanh", "trạm sạc công cộng"],
    "asp_battery": ["pin", "thuê pin", "gói thuê pin", "dung lượng pin", "chai pin", "sạc tại nhà"],
    "asp_software": ["phần mềm", "lỗi vặt", "lỗi phần mềm", "adas", "màn hình", "reset", "trợ lý ảo", "cảm biến", "hệ thống báo lỗi"],
    "asp_comfort": ["lái", "cảm giác lái", "đầm chắc", "vận hành", "cách âm", "ồn", "động cơ", "tăng tốc", "nội thất", "táp lô", "điều hòa", "giảm xóc", "ghế ngồi"],
    "asp_service": ["bảo hành", "cứu hộ", "xưởng dịch vụ", "sửa chữa", "kỹ thuật viên", "showroom", "phụ tùng", "chăm sóc khách hàng"],
    "asp_price": ["giá", "giá bán", "lăn bánh", "khuyến mãi", "ưu đãi", "trả góp", "lãi suất", "voucher", "tiết kiệm", "chi phí vận hành", "kinh tế"]
}

def extract_car_model(text):
    if not isinstance(text, str):
        return "model_other"
    text_lower = text.lower()
    for model_key, keywords in CAR_MODEL_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return model_key
    return "model_other"

def extract_aspect(text):
    if not isinstance(text, str):
        return "asp_other"
    text_lower = text.lower()
    for aspect_key, keywords in ASPECT_KEYWORDS.items():
        if any(kw in text_lower for kw in keywords):
            return aspect_key
    return "asp_other"

def run_lexicon_sentiment(texts):

    results = []
    for text in texts:
        if not isinstance(text, str) or not text.strip():
            results.append(("Trung lập", 0.5))
            continue
            
        tokens = preprocess_vietnamese_text(text, tokenize=True)
        if not tokens:
            results.append(("Trung lập", 0.5))
            continue
            
        if isinstance(tokens, str):
            tokens = tokens.split()
            
        pos_score = 0.0
        neg_score = 0.0
        
        for i, token in enumerate(tokens):
            is_pos = any(word in token for word in POSITIVE_KEYWORDS)
            is_neg = any(word in token for word in NEGATIVE_KEYWORDS)
            
            if not is_pos and not is_neg:
                continue
                
            word_intensity = 1.0
            
            has_intensifier = False
            for j in range(max(0, i-2), i):
                if any(intensifier in tokens[j] for intensifier in INTENSIFIER_WORDS):
                    has_intensifier = True
                    break
            if has_intensifier:
                word_intensity = 1.5
                
            has_negation = False
            for j in range(max(0, i-2), i):
                if any(negation in tokens[j] for negation in NEGATION_WORDS):
                    has_negation = True
                    break
            
            if is_pos:
                if has_negation:
                    neg_score += word_intensity  
                else:
                    pos_score += word_intensity
            elif is_neg:
                if has_negation:
                    pos_score += word_intensity  
                else:
                    neg_score += word_intensity
                    
        is_question = False
        text_lower = text.lower()
        if text.strip().endswith('?'):
            is_question = True
        else:
            question_markers = [
                "cho hỏi", "xin hỏi", "hỏi về", "thế nào", "như thế nào", "sao mọi người",
                "không mọi người", "không cả nhà", "không mọi người ơi", "không nhỉ", "không thế",
                "không vậy", "không hả", "sao thế", "sao vậy", "ai biết", "xin review", "được không", "được không ạ"
            ]
            if any(marker in text_lower for marker in question_markers):
                is_question = True
            else:
                import re
                if re.search(r'\bcó\b.*\bkhông\b', text_lower):
                    is_question = True
        
        if is_question and abs(pos_score - neg_score) <= 1.0:
            results.append(("Trung lập", 0.5))
        elif pos_score > neg_score:
            confidence = min(0.99, 0.6 + (pos_score - neg_score) * 0.1)
            results.append(("Tích cực", confidence))
        elif neg_score > pos_score:
            confidence = min(0.99, 0.6 + (neg_score - pos_score) * 0.1)
            results.append(("Tiêu cực", confidence))
        else:
            results.append(("Trung lập", 0.5))
            
    return results

def run_phobert_sentiment(texts):

    print("[*] Đang tải mô hình PhoBERT (w11wo/phobert-base-vietnamese-sentiment) từ Hugging Face...")
    try:
        from transformers import pipeline
        classifier = pipeline(
            "sentiment-analysis", 
            model="w11wo/phobert-base-vietnamese-sentiment",
            tokenizer="w11wo/phobert-base-vietnamese-sentiment"
        )
        
        results = []
        for i, text in enumerate(texts):
            segmented_text = preprocess_vietnamese_text(text, tokenize=True)
            
            if isinstance(segmented_text, list):
                segmented_str = " ".join(segmented_text)
            else:
                segmented_str = segmented_text
                
            truncated_text = " ".join(segmented_str.split()[:150])
            
            if not truncated_text.strip():
                results.append(("Trung lập", 0.5))
                continue
                
            prediction = classifier(truncated_text)[0]
            label = prediction['label']
            score = prediction['score']
            
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
        print("[!] Tự động chuyển sang thuật toán Lexicon nâng cao (Negation & Intensifiers)...")
        return run_lexicon_sentiment(texts)

def setup_mysql_database():

    print(f"[*] Đang kết nối và khởi tạo Database MySQL tại {MYSQL_HOST}:{MYSQL_PORT}...")
    import pymysql
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        conn.select_db(MYSQL_DATABASE)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_date (
            date_key VARCHAR(8) PRIMARY KEY,
            full_date DATE,
            day INT,
            month INT,
            year INT,
            quarter INT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_source (
            source_key VARCHAR(50) PRIMARY KEY,
            channel_name VARCHAR(100),
            platform VARCHAR(50)
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_sentiment (
            sentiment_key VARCHAR(50) PRIMARY KEY,
            sentiment_label VARCHAR(50),
            confidence_score REAL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_car_model (
            model_key VARCHAR(50) PRIMARY KEY,
            model_name VARCHAR(100) NOT NULL,
            brand VARCHAR(50) NOT NULL,
            segment VARCHAR(50) NOT NULL
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_aspect (
            aspect_key VARCHAR(50) PRIMARY KEY,
            aspect_name VARCHAR(100) NOT NULL,
            description TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_user (
            user_key VARCHAR(50) PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            author_type VARCHAR(20) NOT NULL,
            follower_count INT DEFAULT 0
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_comments (
            comment_key VARCHAR(100) PRIMARY KEY,
            date_key VARCHAR(8),
            source_key VARCHAR(50),
            sentiment_key VARCHAR(50),
            model_key VARCHAR(50),
            aspect_key VARCHAR(50),
            user_key VARCHAR(50),
            comment_text TEXT,
            like_count INT,
            FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
            FOREIGN KEY (source_key) REFERENCES dim_source(source_key),
            FOREIGN KEY (sentiment_key) REFERENCES dim_sentiment(sentiment_key),
            FOREIGN KEY (model_key) REFERENCES dim_car_model(model_key),
            FOREIGN KEY (aspect_key) REFERENCES dim_aspect(aspect_key),
            FOREIGN KEY (user_key) REFERENCES dim_user(user_key)
        )
        """)
        
        conn.commit()
        conn.close()
        print("[+] Khởi tạo Database MySQL thành công!")
    except Exception as e:
        print(f"[!] Lỗi kết nối hoặc cấu hình MySQL: {e}")
        raise e

def load_data_to_dwh(df):

    print("[*] Đang thực hiện ETL: Load dữ liệu vào MySQL Data Warehouse...")
    import pymysql
    try:
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DATABASE,
            charset='utf8mb4'
        )
        cursor = conn.cursor()
        
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        cursor.execute("TRUNCATE TABLE fact_comments")
        cursor.execute("TRUNCATE TABLE dim_date")
        cursor.execute("TRUNCATE TABLE dim_source")
        cursor.execute("TRUNCATE TABLE dim_sentiment")
        cursor.execute("TRUNCATE TABLE dim_car_model")
        cursor.execute("TRUNCATE TABLE dim_aspect")
        cursor.execute("TRUNCATE TABLE dim_user")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        
        car_models = [
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
            ('model_other', 'Khác/Chung', 'Khác', 'Khác')
        ]
        cursor.executemany("""
        INSERT INTO dim_car_model (model_key, model_name, brand, segment)
        VALUES (%s, %s, %s, %s)
        """, car_models)
        
        aspects = [
            ('asp_charging', 'Trạm sạc', 'Số lượng, phân bố, tốc độ sạc, sự tiện lợi của hệ thống trạm sạc'),
            ('asp_battery', 'Pin & Thuê pin', 'Chính sách thuê pin, dung lượng pin, chai pin, sạc tại nhà'),
            ('asp_software', 'Phần mềm & Lỗi vặt', 'Lỗi phần mềm, treo màn hình, ADAS, lỗi ảo, cập nhật firmware'),
            ('asp_comfort', 'Vận hành & Tiện nghi', 'Động cơ, cảm giác lái, cách âm, điều hòa, độ êm ái, nội thất'),
            ('asp_service', 'Dịch vụ & Hậu mãi', 'Chính sách bảo hành, dịch vụ cứu hộ, thái độ showroom, phụ tùng thay thế'),
            ('asp_price', 'Giá bán & Khuyến mãi', 'Giá xe, chương trình ưu đãi, thuế trước bạ, chi phí vận hành so với xe xăng'),
            ('asp_other', 'Khác', 'Các chủ đề thảo luận chung hoặc khía cạnh khác không được phân loại')
        ]
        cursor.executemany("""
        INSERT INTO dim_aspect (aspect_key, aspect_name, description)
        VALUES (%s, %s, %s)
        """, aspects)
        
        for index, row in df.iterrows():
            try:
                dt = datetime.strptime(row['published_at'], "%Y-%m-%dT%H:%M:%SZ")
            except:
                dt = datetime.now()
                
            date_key = dt.strftime("%Y%m%d")
            full_date = dt.strftime("%Y-%m-%d")
            quarter = (dt.month - 1) // 3 + 1
            
            cursor.execute("""
            INSERT IGNORE INTO dim_date (date_key, full_date, day, month, year, quarter)
            VALUES (%s, %s, %s, %s, %s, %s)
            """, (date_key, full_date, dt.day, dt.month, dt.year, quarter))
            
            source_name = row['source']
            platform_name = row.get('platform', 'Social Media')
            source_key = "src_" + platform_name.lower().replace(" ", "_") + "_" + source_name.lower().replace(" ", "_").replace("đ", "d").replace("/", "_").replace("[", "").replace("]", "")
            cursor.execute("""
            INSERT IGNORE INTO dim_source (source_key, channel_name, platform)
            VALUES (%s, %s, %s)
            """, (source_key, source_name, platform_name))
            
            sentiment_key = f"sent_{index}"
            cursor.execute("""
            INSERT IGNORE INTO dim_sentiment (sentiment_key, sentiment_label, confidence_score)
            VALUES (%s, %s, %s)
            """, (sentiment_key, row['sentiment'], float(row['sentiment_score'])))
            
            author_name = row['author']
            author_type = row.get('author_type', 'Regular')
            follower_count = int(row.get('follower_count', 0))
            user_key = "usr_" + str(hash(author_name) % 100000000)
            cursor.execute("""
            INSERT IGNORE INTO dim_user (user_key, username, author_type, follower_count)
            VALUES (%s, %s, %s, %s)
            """, (user_key, author_name, author_type, follower_count))
            
            comment_text = row['comment_text']
            model_key = extract_car_model(comment_text)
            aspect_key = extract_aspect(comment_text)
            
            cursor.execute("""
            INSERT INTO fact_comments (comment_key, date_key, source_key, sentiment_key, model_key, aspect_key, user_key, comment_text, like_count)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                row['comment_id'],
                date_key,
                source_key,
                sentiment_key,
                model_key,
                aspect_key,
                user_key,
                row['comment_text'],
                int(row['like_count'])
            ))
            
        conn.commit()
        conn.close()
        print("[+] Hoàn thành ETL! Dữ liệu đã sẵn sàng trong MySQL DWH.")
    except Exception as e:
        print(f"[!] Lỗi khi chạy ETL nạp MySQL: {e}")
        raise e

def setup_sqlite_database():
    print(f"[*] Đang khởi tạo Database SQLite tại {DB_PATH}...")
    import os
    import sqlite3
    if os.path.exists(DB_PATH):
        try:
            os.remove(DB_PATH)
            print("[+] Đã xóa database SQLite cũ để cập nhật Schema mới.")
        except Exception as e:
            print(f"[!] Cảnh báo: Không thể xóa file DB cũ ({e}). Tiến hành khởi tạo...")
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
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
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_source (
            source_key TEXT PRIMARY KEY,
            channel_name TEXT,
            platform TEXT
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_sentiment (
            sentiment_key TEXT PRIMARY KEY,
            sentiment_label TEXT,
            confidence_score REAL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_car_model (
            model_key TEXT PRIMARY KEY,
            model_name TEXT NOT NULL,
            brand TEXT NOT NULL,
            segment TEXT NOT NULL
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_aspect (
            aspect_key TEXT PRIMARY KEY,
            aspect_name TEXT NOT NULL,
            description TEXT
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS dim_user (
            user_key TEXT PRIMARY KEY,
            username TEXT NOT NULL,
            author_type TEXT NOT NULL,
            follower_count INTEGER DEFAULT 0
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS fact_comments (
            comment_key TEXT PRIMARY KEY,
            date_key TEXT,
            source_key TEXT,
            sentiment_key TEXT,
            model_key TEXT,
            aspect_key TEXT,
            user_key TEXT,
            comment_text TEXT,
            like_count INTEGER,
            FOREIGN KEY (date_key) REFERENCES dim_date(date_key),
            FOREIGN KEY (source_key) REFERENCES dim_source(source_key),
            FOREIGN KEY (sentiment_key) REFERENCES dim_sentiment(sentiment_key),
            FOREIGN KEY (model_key) REFERENCES dim_car_model(model_key),
            FOREIGN KEY (aspect_key) REFERENCES dim_aspect(aspect_key),
            FOREIGN KEY (user_key) REFERENCES dim_user(user_key)
        )
        """)
        
        conn.commit()
        conn.close()
        print("[+] Khởi tạo Database SQLite thành công!")
    except Exception as e:
        print(f"[!] Lỗi khởi tạo SQLite: {e}")
        raise e

def load_data_to_sqlite(df):
    print("[*] Đang thực hiện ETL: Load dữ liệu vào SQLite Data Warehouse...")
    import sqlite3
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA foreign_keys = OFF")
        cursor.execute("DELETE FROM fact_comments")
        cursor.execute("DELETE FROM dim_date")
        cursor.execute("DELETE FROM dim_source")
        cursor.execute("DELETE FROM dim_sentiment")
        cursor.execute("DELETE FROM dim_car_model")
        cursor.execute("DELETE FROM dim_aspect")
        cursor.execute("DELETE FROM dim_user")
        cursor.execute("PRAGMA foreign_keys = ON")
        
        car_models = [
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
            ('model_other', 'Khác/Chung', 'Khác', 'Khác')
        ]
        cursor.executemany("""
        INSERT OR IGNORE INTO dim_car_model (model_key, model_name, brand, segment)
        VALUES (?, ?, ?, ?)
        """, car_models)
        
        aspects = [
            ('asp_charging', 'Trạm sạc', 'Số lượng, phân bố, tốc độ sạc, sự tiện lợi của hệ thống trạm sạc'),
            ('asp_battery', 'Pin & Thuê pin', 'Chính sách thuê pin, dung lượng pin, chai pin, sạc tại nhà'),
            ('asp_software', 'Phần mềm & Lỗi vặt', 'Lỗi phần mềm, treo màn hình, ADAS, lỗi ảo, cập nhật firmware'),
            ('asp_comfort', 'Vận hành & Tiện nghi', 'Động cơ, cảm giác lái, cách âm, điều hòa, độ êm ái, nội thất'),
            ('asp_service', 'Dịch vụ & Hậu mãi', 'Chính sách bảo hành, dịch vụ cứu hộ, thái độ showroom, phụ tùng thay thế'),
            ('asp_price', 'Giá bán & Khuyến mãi', 'Giá xe, chương trình ưu đãi, thuế trước bạ, chi phí vận hành so với xe xăng'),
            ('asp_other', 'Khác', 'Các chủ đề thảo luận chung hoặc khía cạnh khác không được phân loại')
        ]
        cursor.executemany("""
        INSERT OR IGNORE INTO dim_aspect (aspect_key, aspect_name, description)
        VALUES (?, ?, ?)
        """, aspects)
        
        for index, row in df.iterrows():
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
            
            source_name = row['source']
            platform_name = row.get('platform', 'Social Media')
            source_key = "src_" + platform_name.lower().replace(" ", "_") + "_" + source_name.lower().replace(" ", "_").replace("đ", "d").replace("/", "_").replace("[", "").replace("]", "")
            cursor.execute("""
            INSERT OR IGNORE INTO dim_source (source_key, channel_name, platform)
            VALUES (?, ?, ?)
            """, (source_key, source_name, platform_name))
            
            sentiment_key = f"sent_{index}"
            cursor.execute("""
            INSERT OR IGNORE INTO dim_sentiment (sentiment_key, sentiment_label, confidence_score)
            VALUES (?, ?, ?)
            """, (sentiment_key, row['sentiment'], float(row['sentiment_score'])))
            
            author_name = row['author']
            author_type = row.get('author_type', 'Regular')
            follower_count = int(row.get('follower_count', 0))
            user_key = "usr_" + str(hash(author_name) % 100000000)
            cursor.execute("""
            INSERT OR IGNORE INTO dim_user (user_key, username, author_type, follower_count)
            VALUES (?, ?, ?, ?)
            """, (user_key, author_name, author_type, follower_count))
            
            comment_text = row['comment_text']
            model_key = extract_car_model(comment_text)
            aspect_key = extract_aspect(comment_text)
            
            cursor.execute("""
            INSERT INTO fact_comments (comment_key, date_key, source_key, sentiment_key, model_key, aspect_key, user_key, comment_text, like_count)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                row['comment_id'],
                date_key,
                source_key,
                sentiment_key,
                model_key,
                aspect_key,
                user_key,
                row['comment_text'],
                int(row['like_count'])
            ))
            
        conn.commit()
        conn.close()
        print("[+] Hoàn thành ETL! Dữ liệu đã sẵn sàng trong SQLite DWH.")
    except Exception as e:
        print(f"[!] Lỗi khi chạy ETL nạp SQLite: {e}")
        raise e

if __name__ == "__main__":
    if not os.path.exists(RAW_DATA_PATH):
        print(f"[!] Không tìm thấy file {RAW_DATA_PATH}. Đang chạy generate_data.py để sinh dữ liệu...")
        import subprocess
        gen_path = os.path.join(BASE_DIR, "phase_1_crawl", "generate_data.py")
        if not os.path.exists(gen_path):
            gen_path = os.path.join(BASE_DIR, "generate_data.py")
        subprocess.run(["py", gen_path])
        
    df = pd.read_csv(RAW_DATA_PATH)
    
    texts = df['comment_text'].tolist()
    sentiment_results = run_phobert_sentiment(texts)
    
    df['sentiment'] = [res[0] for res in sentiment_results]
    df['sentiment_score'] = [res[1] for res in sentiment_results]
    
    df.to_csv(PROCESSED_DATA_PATH, index=False, encoding="utf-8-sig")
    print(f"[+] Đã lưu dữ liệu đã gán nhãn cảm xúc tại: {PROCESSED_DATA_PATH}")
    
    try:
        setup_mysql_database()
        load_data_to_dwh(df)
    except Exception as e:
        print("[!] Không kết nối được MySQL. Tự động chuyển sang lưu trữ SQLite mặc định...")
        setup_sqlite_database()
        load_data_to_sqlite(df)
