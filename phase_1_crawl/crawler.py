import os
import csv
import pandas as pd
import requests
import sys
import codecs
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

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

# Tạo thư mục chứa dữ liệu nếu chưa tồn tại
os.makedirs("data", exist_ok=True)

# ============================================================================
# CẤU HÌNH THÔNG TIN API & KHÓA TÌM KIẾM
# ============================================================================
YOUTUBE_API_KEY = "YOUR_API_KEY_HERE"  # Thay thế bằng YouTube API Key của bạn
VIDEO_ID = "VF8_REVIEW_VIDEO_ID"       # ID của video cần crawl bình luận

REDDIT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
SEARCH_QUERY = "VinFast"               # Từ khóa tìm kiếm cho Reddit, Twitter, Facebook

TWITTER_BEARER_TOKEN = ""              # Nhập Bearer Token nếu có tài khoản Twitter Developer
FACEBOOK_ACCESS_TOKEN = ""             # Nhập Access Token nếu có tài khoản Facebook Developer

# ============================================================================
# HÀM CRAWL YOUTUBE
# ============================================================================
def crawl_youtube_comments(video_id, api_key, max_comments=150):
    """
    Thu thập bình luận từ một video YouTube dựa trên API Key.
    """
    print(f"[*] Đang bắt đầu thu thập bình luận cho Video ID: {video_id}...")
    comments = []
    
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=100,
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
        print(f"[!] Lỗi không xác định khi crawl YouTube: {e}")
        return None

# ============================================================================
# HÀM CRAWL REDDIT
# ============================================================================
def crawl_reddit_comments(query, max_results=50):
    """
    Thu thập bài viết từ Reddit dựa trên tìm kiếm công khai (public JSON API).
    """
    print(f"[*] Đang bắt đầu thu thập bài viết từ Reddit với từ khóa: '{query}'...")
    headers = {"User-Agent": REDDIT_USER_AGENT}
    url = f"https://www.reddit.com/search.json?q={query}&limit={max_results}"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            posts = []
            for child in data.get('data', {}).get('children', []):
                post_data = child.get('data', {})
                created_utc = post_data.get('created_utc')
                
                # Chuyển đổi timestamp của Reddit sang ISO-8601
                if created_utc:
                    published_at = datetime.fromtimestamp(created_utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                else:
                    published_at = datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ')
                
                title = post_data.get('title', '')
                selftext = post_data.get('selftext', '')
                text = f"{title}\n{selftext}".strip()
                
                posts.append({
                    "comment_id": f"rd_{post_data.get('id', '')}",
                    "author": post_data.get('author', '[deleted]'),
                    "comment_text": text,
                    "published_at": published_at,
                    "like_count": post_data.get('ups', 0),
                    "source": "Reddit"
                })
            
            print(f"[+] Thành công! Đã thu thập được {len(posts)} bài viết từ Reddit.")
            return pd.DataFrame(posts) if posts else None
        else:
            print(f"[!] Lỗi kết nối Reddit API: HTTP {response.status_code}")
            return None
    except Exception as e:
        print(f"[!] Lỗi khi crawl Reddit: {e}")
        return None

# ============================================================================
# HÀM CRAWL TWITTER
# ============================================================================
def crawl_twitter_comments(query, bearer_token=None, max_results=50):
    """
    Thu thập tweet từ Twitter/X sử dụng API v2 Recent Search.
    """
    if not bearer_token or bearer_token == "YOUR_TWITTER_BEARER_TOKEN" or bearer_token.strip() == "":
        print("[!] Không phát hiện Twitter Bearer Token hợp lệ. Bỏ qua crawl Twitter thực tế.")
        return None
        
    print(f"[*] Đang bắt đầu thu thập tweets từ Twitter với từ khóa: '{query}'...")
    url = f"https://api.twitter.com/2/tweets/search/recent?query={query}&max_results={max_results}&tweet.fields=created_at,public_metrics,author_id"
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "User-Agent": "v2RecentSearchPython"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            tweets = []
            for tweet in data.get('data', []):
                public_metrics = tweet.get('public_metrics', {})
                like_count = public_metrics.get('like_count', 0)
                created_at = tweet.get('created_at', datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
                
                tweets.append({
                    "comment_id": f"tw_{tweet.get('id', '')}",
                    "author": f"User_{tweet.get('author_id', '')}",
                    "comment_text": tweet.get('text', ''),
                    "published_at": created_at,
                    "like_count": like_count,
                    "source": "Twitter"
                })
            print(f"[+] Thành công! Đã thu thập được {len(tweets)} tweets từ Twitter.")
            return pd.DataFrame(tweets) if tweets else None
        else:
            print(f"[!] Lỗi kết nối Twitter API: HTTP {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[!] Lỗi khi crawl Twitter: {e}")
        return None

# ============================================================================
# HÀM CRAWL FACEBOOK
# ============================================================================
def crawl_facebook_comments(query, access_token=None, max_results=50):
    """
    Thu thập bài viết từ Facebook sử dụng Graph API.
    Lưu ý: Scraping Facebook không qua API rất dễ bị chặn và khóa IP.
    """
    if not access_token or access_token == "YOUR_FACEBOOK_ACCESS_TOKEN" or access_token.strip() == "":
        print("[!] Không phát hiện Facebook Access Token hợp lệ. Bỏ qua crawl Facebook thực tế.")
        return None
        
    print(f"[*] Đang bắt đầu thu thập bài viết từ Facebook với từ khóa: '{query}'...")
    url = f"https://graph.facebook.com/v18.0/search?q={query}&type=post&limit={max_results}&access_token={access_token}"
    
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            posts = []
            for post in data.get('data', []):
                created_time = post.get('created_time', datetime.now().strftime('%Y-%m-%dT%H:%M:%SZ'))
                posts.append({
                    "comment_id": f"fb_{post.get('id', '')}",
                    "author": post.get('from', {}).get('name', 'Facebook User'),
                    "comment_text": post.get('message', post.get('story', '')),
                    "published_at": created_time,
                    "like_count": post.get('likes', {}).get('summary', {}).get('total_count', 0),
                    "source": "Facebook"
                })
            print(f"[+] Thành công! Đã thu thập được {len(posts)} bài viết từ Facebook.")
            return pd.DataFrame(posts) if posts else None
        else:
            print(f"[!] Lỗi kết nối Facebook API: HTTP {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"[!] Lỗi khi crawl Facebook: {e}")
        return None

# ============================================================================
# HÀM MÔ PHỎNG DỮ LIỆU (MOCK DATA)
# ============================================================================
def generate_mock_comments():
    """
    Tạo dữ liệu mô phỏng tiếng Việt về chủ đề xe điện để chạy demo ngay lập tức 
    khi người dùng chưa cấu hình API Key cho các nguồn.
    """
    print("[*] Đang tạo dữ liệu mô phỏng phong phú từ các nguồn YouTube, Reddit, Twitter, Facebook, Tinh Tế...")
    
    mock_data = [
        # --- YOUTUBE ---
        {"comment_id": "yt_1", "author": "Nguyen An", "comment_text": "Xe VinFast VF3 thiết kế đẹp quá, nhỏ gọn đi phố rất tiện lợi, giá lại hợp lý nữa.", "published_at": "2026-06-10T08:30:00Z", "like_count": 42, "source": "YouTube"},
        {"comment_id": "yt_2", "author": "Tran Binh", "comment_text": "Mình đã chạy thử VF8 được nửa năm, cảm giác lái đầm chắc, tăng tốc sướng tê người.", "published_at": "2026-06-11T12:15:00Z", "like_count": 28, "source": "YouTube"},
        {"comment_id": "yt_3", "author": "Lê Nam", "comment_text": "Ủng hộ xe điện Việt Nam! Bảo vệ môi trường lại tiết kiệm chi phí đổ xăng rất nhiều.", "published_at": "2026-06-13T09:00:00Z", "like_count": 89, "source": "YouTube"},
        {"comment_id": "yt_4", "author": "Thanh Tung", "comment_text": "Xe hay bị lỗi phần mềm vặt, đang đi tự nhiên báo lỗi ảo làm hoang mang ghê.", "published_at": "2026-06-11T16:40:00Z", "like_count": 72, "source": "YouTube"},
        {"comment_id": "yt_5", "author": "Phan Sơn", "comment_text": "Mỗi hãng có một ưu nhược điểm riêng, ai đi phố nhiều thì xe điện hợp lý hơn nhiều.", "published_at": "2026-06-12T15:30:00Z", "like_count": 3, "source": "YouTube"},
        
        # --- TINH TẾ ---
        {"comment_id": "tt_1", "author": "Minh Tuấn", "comment_text": "Chính sách thuê pin của Vin hợp lý, không lo chai pin hay hỏng hóc, dịch vụ cứu hộ cũng nhanh.", "published_at": "2026-06-12T14:45:00Z", "like_count": 15, "source": "Tinh Tế"},
        {"comment_id": "tt_2", "author": "Quốc Khánh", "comment_text": "Hệ thống trạm sạc ở tỉnh vẫn còn ít quá, đi chơi xa cực kỳ bất tiện và lo lắng.", "published_at": "2026-06-10T10:05:00Z", "like_count": 34, "source": "Tinh Tế"},
        {"comment_id": "tt_3", "author": "Ngọc Hải", "comment_text": "Chờ sạc pin mất thời gian quá, đổ xăng chỉ mất 3 phút còn sạc nhanh cũng phải 30 phút.", "published_at": "2026-06-13T20:10:00Z", "like_count": 50, "source": "Tinh Tế"},
        {"comment_id": "tt_4", "author": "Văn Hùng", "comment_text": "Cho mình hỏi chi phí bảo dưỡng xe điện định kỳ khoảng bao nhiêu tiền một năm vậy mọi người?", "published_at": "2026-06-11T07:50:00Z", "like_count": 5, "source": "Tinh Tế"},
        {"comment_id": "tt_5", "author": "Thu Trang", "comment_text": "Nghe nói BYD chuẩn bị xây dựng thêm trạm sạc liên kết đúng không nhỉ?", "published_at": "2026-06-13T13:12:00Z", "like_count": 8, "source": "Tinh Tế"},

        # --- REDDIT ---
        {"comment_id": "rd_1", "author": "reddit_user_99", "comment_text": "VinFast VF3 is highly praised for urban driving. Many users in Vietnam subreddit are sharing their driving experience, mentioning that the compact size is perfect for narrow alleys in Hanoi.", "published_at": "2026-06-12T10:30:00Z", "like_count": 120, "source": "Reddit"},
        {"comment_id": "rd_2", "author": "auto_enthusiast", "comment_text": "So sánh thông số VF8 với các xe xăng cùng tầm giá thì xe điện có lợi thế vượt trội về mô-men xoắn và cảm giác lái. Tuy nhiên trạm sạc ở các khu chung cư vẫn còn là dấu hỏi lớn.", "published_at": "2026-06-13T15:20:00Z", "like_count": 45, "source": "Reddit"},
        {"comment_id": "rd_3", "author": "vn_eco_driver", "comment_text": "Chính sách bảo hành 10 năm của VinFast là điểm cộng rất lớn giúp người tiêu dùng an tâm mua xe, điều mà các hãng xe xăng truyền thống ít khi cam kết.", "published_at": "2026-06-14T09:15:00Z", "like_count": 31, "source": "Reddit"},
        {"comment_id": "rd_4", "author": "tech_guy_hanoi", "comment_text": "Xe điện BYD mới ra mắt ở VN nhìn nội thất rất độc lạ nhưng trạm sạc riêng chưa có nên người mua còn ngại ngần nhiều lắm. Khó cạnh tranh lại VinFast.", "published_at": "2026-06-14T11:40:00Z", "like_count": 67, "source": "Reddit"},
        {"comment_id": "rd_5", "author": "sceptical_driver", "comment_text": "I am still very worried about the battery degradation over years. The renting model reduces initial cost but increases monthly operation cost.", "published_at": "2026-06-15T02:10:00Z", "like_count": 18, "source": "Reddit"},

        # --- TWITTER (X) ---
        {"comment_id": "tw_1", "author": "car_news_vn", "comment_text": "Trải nghiệm lái VinFast VF3: Nhỏ nhưng có võ, tăng tốc mượt mà, xoay xở cực dễ trong phố đông. Rất đáng mua với tầm giá 300 triệu! #VinFast #VF3 #XeDien", "published_at": "2026-06-14T16:00:00Z", "like_count": 150, "source": "Twitter"},
        {"comment_id": "tw_2", "author": "green_move", "comment_text": "BYD chính thức bàn giao lô xe đầu tiên tại VN. Cuộc đua xe điện Việt Nam bắt đầu nóng lên rồi! Hy vọng có thêm nhiều trạm sạc liên kết. #BYD #XeDien", "published_at": "2026-06-14T17:30:00Z", "like_count": 92, "source": "Twitter"},
        {"comment_id": "tw_3", "author": "tech_reviewer", "comment_text": "Lại gặp lỗi phần mềm báo lỗi hệ thống pin ảo trên VF8 lúc đi trời mưa. Vin cần update bản firmware mới gấp chứ đi thế này hoang mang lắm! #VinFast #LoiXeDien", "published_at": "2026-06-15T08:45:00Z", "like_count": 110, "source": "Twitter"},
        {"comment_id": "tw_4", "author": "ev_vietnam", "comment_text": "Xe điện giúp tiết kiệm đến 70% chi phí vận hành so với xe xăng. Một sự đầu tư quá hời cho việc đi lại hàng ngày! #GreenEnergy #EvVietnam", "published_at": "2026-06-15T09:12:00Z", "like_count": 78, "source": "Twitter"},
        {"comment_id": "tw_5", "author": "urban_life", "comment_text": "VF3 nhỏ nhắn xinh xắn nhìn cưng xỉu, chị em đi chợ đi làm che nắng che mưa quá hợp lý luôn nha. #VF3 #VinFast", "published_at": "2026-06-15T10:05:00Z", "like_count": 43, "source": "Twitter"},

        # --- FACEBOOK ---
        {"comment_id": "fb_1", "author": "Hội Chủ Xe VinFast VF3", "comment_text": "Mới lấy em VF3 được 3 ngày, cảm nhận chung là xe đi phố cực kỳ sướng, điều hòa mát lạnh sâu, cách âm tương đối ổn so với tầm giá. Chỉ mong trạm sạc lắp nhiều hơn ở các tỉnh lẻ.", "published_at": "2026-06-13T12:00:00Z", "like_count": 210, "source": "Facebook"},
        {"comment_id": "fb_2", "author": "Trần Minh Hoạt", "comment_text": "Xe BYD Atto 3 đi đầm chắc ghê, nhưng không có trạm sạc nhanh công cộng của hãng thì đi tỉnh mệt lắm các bác ơi. Sạc nhờ ổ cắm gia đình chờ cả đêm mới đầy.", "published_at": "2026-06-14T07:15:00Z", "like_count": 88, "source": "Facebook"},
        {"comment_id": "fb_3", "author": "Nguyễn Khánh Vân", "comment_text": "Chồng em đang phân vân giữa mua VF3 trả thẳng hay trả góp mua VF5. Nhà có 1 con nhỏ đi phố thì xe nào hợp lý hơn ạ? Em thấy VF3 nhìn nhỏ nhắn cute hơn nhiều.", "published_at": "2026-06-14T14:50:00Z", "like_count": 142, "source": "Facebook"},
        {"comment_id": "fb_4", "author": "Lâm Thế Anh", "comment_text": "Dịch vụ cứu hộ pin 24/7 của Vin quá đỉnh. Hôm trước xe hết điện giữa đường gọi 30 phút sau có xe cứu hộ đến sạc hộ ngay. Rất an tâm khi chọn xe điện Vin.", "published_at": "2026-06-15T11:20:00Z", "like_count": 315, "source": "Facebook"},
        {"comment_id": "fb_5", "author": "Báo Cáo Lỗi Xe", "comment_text": "Màn hình trung tâm của VF8 thỉnh thoảng bị đứng hình đen ngóm khi đang khởi động. Phải khóa xe đợi 5 phút reset lại mới lên. Rất khó chịu và mất thời gian.", "published_at": "2026-06-15T13:40:00Z", "like_count": 64, "source": "Facebook"},
    ]
    
    # Tạo thêm khoảng 40 dòng dữ liệu ngẫu nhiên nữa từ các nguồn để phong phú (tổng cộng 65 dòng)
    sources = ["YouTube", "Tinh Tế", "Reddit", "Twitter", "Facebook"]
    brands = ["VinFast VF3", "VinFast VF8", "BYD Atto 3", "Wuling Hongguang", "VinFast VF5"]
    
    pos_phrases = ["chạy rất êm và tiết kiệm", "thiết kế đẹp mắt sang trọng", "dịch vụ hậu mãi rất tốt", "lái đầm chắc sướng lắm", "đáng tiền mua xe điện"]
    neg_phrases = ["bị lỗi phần mềm vặt", "trạm sạc còn quá ít ở tỉnh", "chờ sạc pin lâu bất tiện", "nhựa nội thất lỏng lẻo kém", "giá thuê pin hơi cao"]
    neu_phrases = ["đang tìm hiểu thông số", "cần so sánh xe điện xe xăng", "xin review thực tế đi tỉnh", "đang cân nhắc tài chính", "hãng có hỗ trợ trả góp không"]
    
    for i in range(26, 66):
        source = sources[i % len(sources)]
        brand = brands[i % len(brands)]
        
        if i % 3 == 0:
            text = f"Đánh giá xe {brand}: {pos_phrases[i % len(pos_phrases)]}, ủng hộ xe điện Việt."
            likes = (i * 4) % 120
        elif i % 3 == 1:
            text = f"Xe {brand} còn {neg_phrases[i % len(neg_phrases)]}, hy vọng hãng sớm cải thiện."
            likes = (i * 9) % 150
        else:
            text = f"Mình {neu_phrases[i % len(neu_phrases)]} đối với chiếc {brand} này."
            likes = (i * 2) % 30
            
        mock_data.append({
            "comment_id": f"mock_{source.lower()[:2]}_{i}",
            "author": f"User_{source[:2]}_{i}",
            "comment_text": text,
            "published_at": f"2026-06-{10 + (i%6):02d}T{10 + (i%12):02d}:00:00Z",
            "like_count": likes,
            "source": source
        })
        
    return pd.DataFrame(mock_data)

# ============================================================================
# LUỒNG CHẠY CHÍNH (MAIN ENTRYPOINT)
# ============================================================================
if __name__ == "__main__":
    dfs = []
    
    # 1. Thu thập từ YouTube
    if YOUTUBE_API_KEY and YOUTUBE_API_KEY != "YOUR_API_KEY_HERE":
        df_yt = crawl_youtube_comments(VIDEO_ID, YOUTUBE_API_KEY)
        if df_yt is not None and not df_yt.empty:
            dfs.append(df_yt)
            
    # 2. Thu thập từ Reddit
    df_reddit = crawl_reddit_comments(SEARCH_QUERY)
    if df_reddit is not None and not df_reddit.empty:
        dfs.append(df_reddit)
        
    # 3. Thu thập từ Twitter
    if TWITTER_BEARER_TOKEN and TWITTER_BEARER_TOKEN != "YOUR_TWITTER_BEARER_TOKEN":
        df_twitter = crawl_twitter_comments(SEARCH_QUERY, TWITTER_BEARER_TOKEN)
        if df_twitter is not None and not df_twitter.empty:
            dfs.append(df_twitter)
            
    # 4. Thu thập từ Facebook
    if FACEBOOK_ACCESS_TOKEN and FACEBOOK_ACCESS_TOKEN != "YOUR_FACEBOOK_ACCESS_TOKEN":
        df_fb = crawl_facebook_comments(SEARCH_QUERY, FACEBOOK_ACCESS_TOKEN)
        if df_fb is not None and not df_fb.empty:
            dfs.append(df_fb)
            
    # Hợp nhất các DataFrame kết quả
    if dfs:
        df = pd.concat(dfs, ignore_index=True)
    else:
        # Nếu không thu thập được từ nguồn thực tế nào, sinh dữ liệu mô phỏng
        df = generate_mock_comments()
        
    # Lưu kết quả ra file raw CSV
    output_path = os.path.join("data", "raw_comments.csv")
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"[+] Đã lưu tổng cộng {len(df)} dòng dữ liệu thô vào file: {output_path}")
