import pandas as pd
import re

car_keywords = [
    r'\bvf\d\b', r'\bvf\s\d\b', r'\bvfe34\b', r'\bvf e34\b', r'\bvinfast\b', r'\bvin\b', 
    r'\bwuling\b', r'\bmini ev\b', r'\bioniq\b', r'\bporsche\b', r'\btesla\b', r'\bbyd\b',
    r'\bmg\b', r'\bhonda\b', r'\btoyota\b', r'\bhyundai\b', r'\bkia\b', r'\bmazda\b', r'\bford\b',
    
    r'\bxe\b', r'\bpin\b', r'\bsạc\b', r'\btrạm sạc\b', r'\bô tô\b', r'\boto\b', r'\bđộng cơ\b', 
    r'\blốp\b', r'\bmâm\b', r'\bla zăng\b', r'\blazang\b', r'\bphuộc\b', r'\btreo\b', r'\bkhung gầm\b', r'\bcốp\b',
    r'\bghế\b', r'\bda\b', r'\bmàn hình\b', r'\bvô lăng\b', r'\bcửa\b', r'\btrần\b', r'\bkiếng\b', r'\bkính\b',
    r'\bgương\b', r'\bphanh\b', r'\bthắng\b', r'\bcam\b', r'\bcamera\b', r'\bcảm biến\b', r'\btrục cơ sở\b',
    r'\bgầm\b', r'\bgiảm xóc\b', r'\bchìa khóa\b', r'\bđiều hòa\b', r'\bmáy lạnh\b',
    
    r'\bso sánh\b', r'\bgiá\b', r'\blái\b', r'\bcách âm\b', r'\bồn\b', r'\bêm\b', r'\bmượt\b', r'\bbốc\b',
    r'\bxóc\b', r'\bchòng chành\b', r'\bbồng bềnh\b', r'\btrọng tâm\b', r'\btốc độ\b', r'\bkm/h\b',
    r'\bmô men\b', r'\bmomen\b', r'\bcông suất\b', r'\bmã lực\b', r'\bhao\b', r'\btiết kiệm\b', r'\bdung lượng\b',
    r'\bcông nghệ\b', r'\btrang bị\b', r'\bphần mềm\b', r'\bcập nhật\b', r'\blỗi\b', r'\badas\b', 
    r'\bthông minh\b', r'\btự lái\b', r'\bchống ồn\b', r'\ban toàn\b', r'\bcảnh báo\b', r'\bphạm vi\b', r'\bquãng đường\b',
    
    r'\bđèn\b', r'\bpha\b', r'\bcos\b', r'\bxi nhan\b', r'\bled\b', r'\bhậu\b', r'\bsương mù\b', r'\bchiếu sáng\b',
    
    r'\bxăng\b', r'\bđiện\b', r'\bdầu\b', r'\bđổ xăng\b', r'\bsạc điện\b', r'\bhybrid\b',
    
    r'\blăn bánh\b', r'\bkhuyến mãi\b', r'\bcọc\b', r'\bgiao xe\b', r'\bbảo hành\b', r'\bbảo dưỡng\b', 
    r'\bthuê pin\b', r'\bmua pin\b', r'\bchi phí\b', r'\bsale\b', r'\bđại lý\b', r'\bshowroom\b', r'\btrả góp\b',
    r'\bmua\b', r'\bbán\b', r'\bchính sách\b', r'\bthu cũ\b', r'\bđổi mới\b',
    
    r'\bthiết kế\b', r'\bngoại thất\b', r'\bnội thất\b', r'\brộng\b', r'\bchật\b', r'\bđẹp\b', r'\bxấu\b'
]
car_pattern = re.compile('|'.join(car_keywords), re.IGNORECASE)
# HARD BLACKLIST 
hard_spam_keywords = [
    r'http[s]?://\S+', r'www\.\S+', r'\bbit\.ly\S*', r'\bzalo\.me\S*', r'\bfb\.com\S*', r'\bfacebook\.com\S*',
    r'\.com\/\S*', r'\.vn\/\S*', r'\.net\/\S*', r'link\s*bên\s*dưới', r'link\s*ở\s*dưới', r'link\s*tiểu\s*sử',
    r'nhóm\s*zalo', r'group\s*zalo', r'vào\s*nhóm', r'kéo\s*nhóm', r'zalo\s*0\d{8,9}\b', r'sđt\s*0\d{8,9}\b',
    r'zalo', r'\bfb\b', r'\bfacebook\b', r'\blink\b', r'\btiểu\s*sử\b', r'\bprofile\b', r'\bnick\b',
    
    r'\blô đề\b', r'\bsoi cầu\b', r'\bchốt số\b', r'\btài xỉu\b', r'\bcá độ\b', r'\bcá cược\b', r'\bbóng bánh\b',
    r'\bnhà cái\b', r'\bcasino\b', r'\bkubet\b', r'\bku\s*casino\b', r'\bsunwin\b', r'\bgo88\b', r'\bbet88\b',
    r'\bw88\b', r'\bm88\b', r'\bnổ hũ\b', r'\bbaccarat\b', r'\bxóc đĩa\b', r'\bđánh bài\b', r'\bkèo\b',
    r'\btặng code\b', r'\bnhận code\b', r'\bgame bài\b',
    
    r'\bvay tiền\b', r'\bcho vay\b', r'\btín dụng\b', r'\bbốc bát họ\b', r'\bapp vay\b', r'\bkhông cần thế chấp\b',
    r'\bviệc làm tại nhà\b', r'\bkiếm tiền online\b', r'\bđầu tư sinh lời\b', r'\bchứng khoán\b', r'\bforex\b',
    r'\btiền ảo\b', r'\bhoa hồng\b', r'\blãi suất\b', r'\bcầm đồ\b',
    r'\bđông y\b', r'\bnhà thuốc\b', r'\bchữa bệnh\b', r'\bthuốc trị\b', r'\bcam kết khỏi\b',
    
    r'\b18\+\b', r'\bsex\b', r'\bsinh lý\b', r'\bphim hay\b', r'\bnhạc hay\b', r'\btải game\b', r'\blink phim\b'
]
hard_spam_pattern = re.compile('|'.join(hard_spam_keywords), re.IGNORECASE)


seeding_keywords = [
    r'inbox', r'\bib\b', r'check\s*ib', r'nhắn\s*tin', r'kết\s*bạn', r'rep\s*inbox',
    r'qua\s*tường', r'vào\s*trang\s*cá\s*nhân', r'ghé\s*kênh', r'xem\s*kênh\s*mình', r'follow',
    
    r'(kênh|video|review|clip|ad|admin|bác|anh|em|chú|mc|chị)\s*(này\s*)?(rất\s|quá\s)?(hay|ok|xịn|tuyệt|bổ ích|đỉnh|chất|chuẩn|tâm huyết|tuyệt vời|thực tế|chi tiết)',
    r'khen\s*(video|kênh|review)\s*(hay|tuyệt|quá)',
    r'hay\s*quá', r'tuyệt\s*vời', r'quá\s*tuyệt', r'đỉnh\s*quá', r'xuất\s*sắc', r'quá\s*đỉnh', r'đỉnh\s*của\s*chóp',
    r'xem\s*cuốn\s*quá', r'rất\s*thực\s*tế', r'rất\s*chi\s*tiết', r'ủng\s*hộ\s*anh',
    
    r'chúc\s*(kênh|ad|admin|video|anh|em|bác|chị|mọi\s*người|cả\s*nhà)',
    r'cảm\s*ơn\s*(kênh|ad|admin|anh|em|bác|chị)',
    r'ủng\s*hộ\s*(kênh|ad|admin|bác|anh|em|chị)',
    r'phát\s*triển', r'ra\s*thêm\s*(nhiều\s*)?video', r'thành\s*công', r'sức\s*khỏe', r'nhiều\s*người\s*xem',
    
    r'hóng', r'tym', r'❤️', r'👍', r'lên\s*xu\s*hướng', r'chấm', r'\.\.\.', r'hihi', r'haha', r'kkk', r'hehe',
    r'tương\s*tác', r'sub', r'đăng\s*ký', r'đã\s*đăng\s*ký', r'xem\s*ké', r'nghe\s*nhạc', r'chào\s*mọi\s*người',
    r'chào\s*các\s*bác', r'xin\s*chào', r'1\s*like', r'cho\s*1\s*like', r'tym\s*cho',
    r'triệu\s*view', r'triệu\s*sub', r'view', r'luôn\s*theo\s*dõi', r'mai\s*theo\s*dõi', r'đã\s*like'
]
seeding_pattern = re.compile('|'.join(seeding_keywords), re.IGNORECASE)

foreign_lang_pattern = re.compile(r'[\u4e00-\u9fff\u3040-\u30ff\uac00-\ud7af\u0400-\u04ff\u0600-\u06ff\u0e00-\u0e7f\u0900-\u097f]')

#filter function delete comment with specific patterns
def filter_comment(text):
    text_str = str(text)
    
    if text_str.strip() == '' or text_str.lower() == 'nan':
        return False
        
    if foreign_lang_pattern.search(text_str):
        return False
    
    if hard_spam_pattern.search(text_str):
        return False
        
    if car_pattern.search(text_str):
        return True
        
    if seeding_pattern.search(text_str):
        return False
        
    words = text_str.split()
    if len(words) < 4:
        return False
        
    return True

# python phase_2_preprocess/filter_youtube_data.py
df = pd.read_csv('data/youtube_comments.csv')
df = df.dropna(subset=['text']).copy()

df['is_relevant'] = df['text'].apply(filter_comment)

kept_comments = df[df['is_relevant'] == True].drop(columns=['is_relevant'])
kept_comments.to_csv('data/filtered_youtube_comments.csv', index=False)