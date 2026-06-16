import re
import unicodedata
from underthesea import word_tokenize
import pandas as pd
import emoji

import sys
import codecs

if sys.platform.startswith('win'):
    # Đảm bảo console ghi nhận tiếng Việt UTF-8 không lỗi trên Windows
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

try:
    from underthesea import word_tokenize
    UNDERTHESEA_AVAILABLE = True
except ImportError:
    UNDERTHESEA_AVAILABLE = False
    
# Từ điển ánh xạ từ viết tắt, tiếng lóng tiếng Việt thường gặp
VIETNAMESE_SLANGS = {
    "ko": "không",
    "k": "không",
    "khg": "không",
    "kg": "không",
    "dc": "được",
    "đc": "được",
    "gút": "tốt",
    "good": "tốt",
    "ok": "tốt",
    "oke": "tốt",
    "okay": "tốt",
    "vfs": "vinfast",
    "vf": "vinfast",
    "vf3": "vinfast vf3",
    "vf5": "vinfast vf5",
    "vf6": "vinfast vf6",
    "vf7": "vinfast vf7",
    "vf8": "vinfast vf8",
    "vf9": "vinfast vf9",
    "vfe34": "vinfast vfe34",
    "e34": "vinfast vfe34",
    "đt": "điện thoại",
    "tks": "cảm ơn",
    "thanks": "cảm ơn",
    "cảm ơn": "cảm ơn",
    "cám ơn": "cảm ơn",
    "qúa": "quá",
    "ae": "anh em",
    "e": "em",
    "mình": "mình",
    "mh": "mình",
    "nv": "nhân viên",
    "fb": "facebook",
    "ytb": "youtube",
    "vs": "với",
    "r": "rồi",
    "rùi": "rồi",
    "j": "gì",
}

def normalize_unicode(text):
    """
    Chuẩn hóa định dạng Unicode (NFC) tránh lỗi font tiếng Việt dựng sẵn/tổ hợp.
    """
    return unicodedata.normalize('NFC', text)

def clean_text(text):
    """
    Làm sạch các ký tự đặc biệt, URL, email, đưa văn bản về chữ thường.
    """
    if not isinstance(text, str):
        return ""
        
    text = normalize_unicode(text)
    
    # Chuyển về chữ thường
    text = text.lower()
    
    # Loại bỏ các đường dẫn liên kết (URLs)
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Loại bỏ địa chỉ email
    text = re.sub(r'\S+@\S+', '', text)
    
    # Loại bỏ ký tự đặc biệt, giữ lại chữ cái tiếng Việt, số, khoảng trắng
    # Bao gồm cả các chữ có dấu tiếng Việt
    text = re.sub(r'[^a-z0-9A-Z_àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệđìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ\s]', ' ', text)
    
    # Thay thế nhiều dấu cách bằng một khoảng trắng duy nhất
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def replace_slangs(text):
    """
    Thay thế các từ viết tắt và từ lóng bằng từ chuẩn tiếng Việt.
    """
    words = text.split()
    normalized_words = [VIETNAMESE_SLANGS.get(w, w) for w in words]
    return " ".join(normalized_words)

def remove_emojis_regex(text):
    """
    Xóa sạch mọi ký tự không phải chữ cái tiếng Việt, số, hoặc khoảng trắng.
    Không cần dùng thư viện emoji.
    """
    if not isinstance(text, str):
        return ""
    
    # Bước 1: Chuyển về chữ thường để dễ xử lý
    text = text.lower()
    
    # Bước 2: Regex Tối Thượng - Chỉ giữ lại đúng a-z, 0-9, dấu cách và chữ tiếng Việt
    # Bất cứ ký tự nào khác (icon, dấu câu, ký tự lạ) sẽ bị biến thành khoảng trắng
    text = re.sub(r'[^a-z0-9_àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệđìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ\s]', ' ', text)
    
    # Bước 3: Dọn dẹp khoảng trắng thừa
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def preprocess_vietnamese_text(text, tokenize=True):
    """
    Toàn bộ pipeline tiền xử lý văn bản tiếng Việt.
    """
    
    text_with_translated_emojis = remove_emojis_regex(text)

    # 1. Làm sạch văn bản thô
    cleaned = clean_text(text_with_translated_emojis)
    
    # 2. Chuẩn hóa tiếng lóng/viết tắt
    normalized = replace_slangs(cleaned)
    
    if not normalized:
        return ""
        
    # 3. Tách từ tiếng Việt bằng underthesea (Word Segmentation)
    if tokenize:
        if UNDERTHESEA_AVAILABLE:
            # format="fixed" nối các từ ghép bằng dấu gạch dưới (ví dụ: "xe_điện")
            tokens = word_tokenize(normalized, format="fixed")
            return tokens
        else:
            # Fallback sang tách từ bằng khoảng trắng nếu không có underthesea
            return normalized.split()
        
    return normalized


if __name__ == "__main__":
    # 1. Định nghĩa đường dẫn file và tên cột cần xử lý
    # (Bạn hãy thay đổi tên file và tên cột cho khớp với dữ liệu thực tế)
    csv_file_path = 'data/filtered_youtube_comments.csv'
    text_column_name = 'text' 
    
    try:
        # 2. Đọc file CSV vào Pandas DataFrame
        df = pd.read_csv(csv_file_path, encoding='utf-8')
        print(f"Đã tải thành công {len(df)} dòng dữ liệu từ {csv_file_path}.\n")
        
        # Khởi tạo một mảng để lưu kết quả sau khi xử lý
        processed_results = []
        
        # 3. Lặp để duyệt từng dòng (iterrows) và xử lý
        print("Đang tiến hành xử lý dữ liệu...")
        for index, row in df.iterrows():
            # Lấy nội dung bình luận, ép kiểu về string để tránh lỗi với giá trị NaN/Null
            original_text = str(row[text_column_name])
            
            # Đưa qua pipeline tiền xử lý của bạn
            processed_text = preprocess_vietnamese_text(original_text, tokenize=True)
            
            # Thêm kết quả vào mảng
            processed_results.append(processed_text)
            
            # (Tùy chọn) In ra 3 dòng đầu tiên để trực quan hóa kết quả test
            # if index < 3:
            #     print(f"--- Dòng {index + 1} ---")
            #     print(f"Gốc    : {original_text}")
            #     print(f"Đã xử lý: {processed_text}\n")
                
        # 4. Gắn danh sách kết quả thành một cột mới trong DataFrame
        df['processed_comment'] = processed_results
        
        # 5. Xuất kết quả ra một file CSV mới (utf-8-sig để Excel không bị lỗi font tiếng Việt)
        output_file = 'data/processed_comments.csv'
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Đã hoàn thành! Kết quả được lưu tại: {output_file}")
        
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file '{csv_file_path}'. Vui lòng kiểm tra lại tên hoặc đường dẫn.")
    except KeyError:
        print(f"Lỗi: File CSV không chứa cột nào tên là '{text_column_name}'. Vui lòng kiểm tra lại dữ liệu.")
    except Exception as e:
        print(f"Có lỗi bất ngờ xảy ra: {e}")
