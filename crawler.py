import os
import csv
import pandas as pd
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Tạo thư mục chứa dữ liệu nếu chưa tồn tại
os.makedirs("data", exist_ok=True)

# THÔNG TIN CẤU HÌNH YOUTUBE
# Thay thế API Key và Video ID thực tế của bạn tại đây
YOUTUBE_API_KEY = "YOUR_API_KEY_HERE"  # Để trống hoặc giữ nguyên để tự động chạy dữ liệu mô phỏng
VIDEO_ID = "VF8_REVIEW_VIDEO_ID"       # ID của video cần crawl bình luận

def crawl_youtube_comments(video_id, api_key, max_comments=150):
    """
    Thu thập bình luận từ một video YouTube dựa trên API Key.
    """
    print(f"[*] Đang bắt đầu thu thập bình luận cho Video ID: {video_id}...")
    comments = []
    
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        # Gọi API lấy các danh sách bình luận (commentThreads)
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,  # Tối đa 100 kết quả mỗi page
            textFormat="plainText"
        )
        
        while request and len(comments) < max_comments:
            response = request.execute()
            
            for item in response.get('items', []):
                snippet = item['snippet']['topLevelComment']['snippet']
                comment_text = snippet['textDisplay']
                author = snippet['authorDisplayName']
                published_at = snippet['publishedAt']
                like_count = snippet['likeCount']
                
                comments.append({
                    "comment_id": item['id'],
                    "author": author,
                    "comment_text": comment_text,
                    "published_at": published_at,
                    "like_count": like_count,
                    "source": "YouTube"
                })
                
                if len(comments) >= max_comments:
                    break
            
            # Kiểm tra xem có trang tiếp theo (nextPageToken) không
            if 'nextPageToken' in response and len(comments) < max_comments:
                request = youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    maxResults=100,
                    pageToken=response['nextPageToken'],
                    textFormat="plainText"
                )
            else:
                break
                
        print(f"[+] Thành công! Đã thu thập được {len(comments)} bình luận từ YouTube API.")
        return pd.DataFrame(comments)
        
    except HttpError as e:
        print(f"[!] Lỗi kết nối YouTube API: {e}")
        return None
    except Exception as e:
        print(f"[!] Lỗi không xác định: {e}")
        return None

def generate_mock_comments():
    """
    Tạo dữ liệu mô phỏng tiếng Việt về chủ đề xe điện để chạy demo ngay lập tức 
    khi người dùng chưa có hoặc chưa điền API Key.
    """
    print("[*] Không phát hiện API Key hợp lệ. Đang tạo dữ liệu mô phỏng về xe điện tại Việt Nam...")
    
    mock_data = [
        # Tích cực
        {"comment_id": "c1", "author": "Nguyen An", "comment_text": "Xe VinFast VF3 thiết kế đẹp quá, nhỏ gọn đi phố rất tiện lợi, giá lại hợp lý nữa.", "published_at": "2026-06-10T08:30:00Z", "like_count": 42, "source": "Tinh Tế"},
        {"comment_id": "c2", "author": "Tran Binh", "comment_text": "Mình đã chạy thử VF8 được nửa năm, cảm giác lái đầm chắc, tăng tốc sướng tê người.", "published_at": "2026-06-11T12:15:00Z", "like_count": 28, "source": "YouTube"},
        {"comment_id": "c3", "author": "Minh Tuấn", "comment_text": "Chính sách thuê pin của Vin hợp lý, không lo chai pin hay hỏng hóc, dịch vụ cứu hộ cũng nhanh.", "published_at": "2026-06-12T14:45:00Z", "like_count": 15, "source": "Tinh Tế"},
        {"comment_id": "c4", "author": "Lê Nam", "comment_text": "Ủng hộ xe điện Việt Nam! Bảo vệ môi trường lại tiết kiệm chi phí đổ xăng rất nhiều.", "published_at": "2026-06-13T09:00:00Z", "like_count": 89, "source": "YouTube"},
        {"comment_id": "c5", "author": "Hoàng Vy", "comment_text": "VF3 nhìn cute thật sự, đi làm đi chợ che nắng che mưa quá đỉnh cho chị em.", "published_at": "2026-06-14T18:22:00Z", "like_count": 56, "source": "YouTube"},
        
        # Tiêu cực
        {"comment_id": "c6", "author": "Quốc Khánh", "comment_text": "Hệ thống trạm sạc ở tỉnh vẫn còn ít quá, đi chơi xa cực kỳ bất tiện và lo lắng.", "published_at": "2026-06-10T10:05:00Z", "like_count": 34, "source": "Tinh Tế"},
        {"comment_id": "c7", "author": "Thanh Tung", "comment_text": "Xe hay bị lỗi phần mềm vặt, đang đi tự nhiên báo lỗi ảo làm hoang mang ghê.", "published_at": "2026-06-11T16:40:00Z", "like_count": 72, "source": "YouTube"},
        {"comment_id": "c8", "author": "Duy Manh", "comment_text": "Giá xe điện BYD về Việt Nam vẫn còn cao quá, khó cạnh tranh với xe xăng cùng phân khúc.", "published_at": "2026-06-12T11:20:00Z", "like_count": 11, "source": "YouTube"},
        {"comment_id": "c9", "author": "Ngọc Hải", "comment_text": "Chờ sạc pin mất thời gian quá, đổ xăng chỉ mất 3 phút còn sạc nhanh cũng phải 30 phút.", "published_at": "2026-06-13T20:10:00Z", "like_count": 50, "source": "Tinh Tế"},
        {"comment_id": "c10", "author": "Anh Đức", "comment_text": "Chất lượng hoàn thiện nhựa nội thất của xe hơi lỏng lẻo, chưa xứng đáng tầm tiền.", "published_at": "2026-06-14T22:05:00Z", "like_count": 19, "source": "YouTube"},
        
        # Trung lập
        {"comment_id": "c11", "author": "Văn Hùng", "comment_text": "Cho mình hỏi chi phí bảo dưỡng xe điện định kỳ khoảng bao nhiêu tiền một năm vậy mọi người?", "published_at": "2026-06-11T07:50:00Z", "like_count": 5, "source": "Tinh Tế"},
        {"comment_id": "c12", "author": "Phan Sơn", "comment_text": "Mỗi hãng có một ưu nhược điểm riêng, ai đi phố nhiều thì xe điện hợp lý hơn nhiều.", "published_at": "2026-06-12T15:30:00Z", "like_count": 3, "source": "YouTube"},
        {"comment_id": "c13", "author": "Thu Trang", "comment_text": "Nghe nói BYD chuẩn bị xây dựng thêm trạm sạc liên kết đúng không nhỉ?", "published_at": "2026-06-13T13:12:00Z", "like_count": 8, "source": "Tinh Tế"},
        {"comment_id": "c14", "author": "Hoàng Long", "comment_text": "Đang phân vân giữa mua VF3 trả thẳng hay mua xe xăng cũ đi gia đình.", "published_at": "2026-06-14T10:00:00Z", "like_count": 12, "source": "YouTube"},
        {"comment_id": "c15", "author": "Kim Oanh", "comment_text": "Nhà chung cư không có chỗ sạc riêng thì dùng xe điện sẽ hơi bất tiện một chút.", "published_at": "2026-06-15T08:05:00Z", "like_count": 25, "source": "YouTube"},
    ]
    
    # Tạo thêm khoảng 45 comment ngẫu nhiên nữa để dữ liệu phong phú (tổng cộng 60 comment)
    brands = ["VinFast VF3", "VinFast VF8", "BYD Atto 3", "Xiaomi SU7", "Wuling Hongguang"]
    pos_phrases = ["rất tốt", "quá tuyệt vời", "tiết kiệm nhiên liệu", "vận hành êm ái", "mẫu mã sang trọng", "đáng mua"]
    neg_phrases = ["lỗi sạc pin", "dịch vụ kém", "quá đắt đỏ", "lỗi hệ thống", "chờ sạc mệt mỏi", "chất lượng kém"]
    neu_phrases = ["đang cân nhắc", "có ai dùng chưa", "xin thông số kỹ thuật", "so sánh thử xem", "tùy nhu cầu thôi"]
    
    for i in range(16, 61):
        brand = brands[i % len(brands)]
        if i % 3 == 0: # Positive
            text = f"Mình đánh giá xe {brand} {pos_phrases[i % len(pos_phrases)]}, đi rất sướng."
            likes = (i * 3) % 40
        elif i % 3 == 1: # Negative
            text = f"Xe {brand} còn nhiều {neg_phrases[i % len(neg_phrases)]}, cần cải thiện nhiều."
            likes = (i * 7) % 50
        else: # Neutral
            text = f"Mọi người cho mình {neu_phrases[i % len(neu_phrases)]} về dòng xe {brand} này nhé."
            likes = (i * 2) % 15
            
        mock_data.append({
            "comment_id": f"c{i}",
            "author": f"User {i}",
            "comment_text": text,
            "published_at": f"2026-06-{10 + (i%6):02d}T{10 + (i%12):02d}:00:00Z",
            "like_count": likes,
            "source": "YouTube" if i % 2 == 0 else "Tinh Tế"
        })
        
    return pd.DataFrame(mock_data)

if __name__ == "__main__":
    df = None
    if YOUTUBE_API_KEY and YOUTUBE_API_KEY != "YOUR_API_KEY_HERE":
        df = crawl_youtube_comments(VIDEO_ID, YOUTUBE_API_KEY)
    
    # Nếu không crawl được hoặc API key chưa thiết lập, sinh dữ liệu mô phỏng
    if df is None:
        df = generate_mock_comments()
        
    # Lưu kết quả ra file raw CSV
    output_path = os.path.join("data", "raw_comments.csv")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[+] Đã lưu dữ liệu thô vào file: {output_path}")
