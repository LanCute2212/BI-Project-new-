import re
import unicodedata
from underthesea import word_tokenize
import pandas as pd

import sys
import codecs

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

try:
    from underthesea import word_tokenize
    UNDERTHESEA_AVAILABLE = True
except ImportError:
    UNDERTHESEA_AVAILABLE = False
    
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
    
    text = text.lower()
    
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    text = re.sub(r'\S+@\S+', '', text)
    
    text = re.sub(r'[^a-z0-9A-Z_àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệđìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ\s]', ' ', text)
    
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def replace_slangs(text):

    words = text.split()
    normalized_words = [VIETNAMESE_SLANGS.get(w, w) for w in words]
    return " ".join(normalized_words)

def remove_emojis_regex(text):

    if not isinstance(text, str):
        return ""
    
    text = text.lower()
    
    text = re.sub(r'[^a-z0-9_àáảãạâầấẩẫậăằắẳẵặèéẻẽẹêềếểễệđìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵ\s]', ' ', text)
    
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def preprocess_vietnamese_text(text, tokenize=True):

    
    text_with_translated_emojis = remove_emojis_regex(text)

    cleaned = clean_text(text_with_translated_emojis)
    
    normalized = replace_slangs(cleaned)
    
    if not normalized:
        return ""
        
    if tokenize:
        if UNDERTHESEA_AVAILABLE:
            tokens = word_tokenize(normalized, format="fixed")
            return tokens
        else:
            return normalized.split()
        
    return normalized


if __name__ == "__main__":
    csv_file_path = 'data/filtered_youtube_comments.csv'
    text_column_name = 'text' 
    
    try:
        df = pd.read_csv(csv_file_path, encoding='utf-8')
        print(f"Đã tải thành công {len(df)} dòng dữ liệu từ {csv_file_path}.\n")
        
        processed_results = []
        
        print("Đang tiến hành xử lý dữ liệu...")
        for index, row in df.iterrows():
            original_text = str(row[text_column_name])
            
            processed_text = preprocess_vietnamese_text(original_text, tokenize=True)
            
            processed_results.append(processed_text)
            
            # (Tùy chọn) In ra 3 dòng đầu tiên để trực quan hóa kết quả test
            # if index < 3:
            #     print(f"--- Dòng {index + 1} ---")
            #     print(f"Gốc    : {original_text}")
            #     print(f"Đã xử lý: {processed_text}\n")
                
        df['processed_comment'] = processed_results
        
        output_file = 'data/processed_comments.csv'
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"Đã hoàn thành! Kết quả được lưu tại: {output_file}")
        
    except FileNotFoundError:
        print(f"Lỗi: Không tìm thấy file '{csv_file_path}'. Vui lòng kiểm tra lại tên hoặc đường dẫn.")
    except KeyError:
        print(f"Lỗi: File CSV không chứa cột nào tên là '{text_column_name}'. Vui lòng kiểm tra lại dữ liệu.")
    except Exception as e:
        print(f"Có lỗi bất ngờ xảy ra: {e}")
