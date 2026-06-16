import re
import unicodedata
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

def preprocess_vietnamese_text(text, tokenize=True):
    """
    Toàn bộ pipeline tiền xử lý văn bản tiếng Việt.
    """
    # 1. Làm sạch văn bản thô
    cleaned = clean_text(text)
    
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
    # Test thử tiền xử lý
    test_comment = "Xe VF3 đi ok lắm nha ae, ko bị lỗi vặt tí nào cả 👍!!! Link review: http://example.com"
    print("Bình luận gốc:", test_comment)
    print("Sau tiền xử lý:", preprocess_vietnamese_text(test_comment, tokenize=True))
