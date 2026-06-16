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

df_credentials = pd.read_json('credential.json')

YOUTUBE_API_KEY = df_credentials['YOUTUBE_API_KEY'].iloc[0]  # Lấy API Key từ file credential.json
         # ID của video cần crawl bình luận
REDDIT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
SEARCH_QUERY = df_credentials['SEARCH_QUERY'].iloc[0]   # Từ khóa tìm kiếm cho Reddit, Twitter, Facebook

TWITTER_BEARER_TOKEN = df_credentials['TWITTER_BEARER_TOKEN'].iloc[0]  # Nhập Bearer Token nếu có tài khoản Twitter Developer
FACEBOOK_ACCESS_TOKEN = df_credentials['FACEBOOK_ACCESS_TOKEN'].iloc[0] # Nhập Access Token nếu có tài khoản Facebook Developer

import json
import os
import time
import pandas as pd
from googleapiclient.discovery import build


def load_credentials(file_path='credentials.json'):
    """Hàm kiểm tra và đọc file credentials"""
    if not os.path.exists(file_path):
        raise FileNotFoundError(
            f"Không tìm thấy file '{file_path}'. Hãy chắc chắn bạn đã tạo file này và đặt đúng vị trí."
        )
        
    with open(file_path, 'r', encoding='utf-8') as f:
        credentials = json.load(f)
        
    return credentials

def search_smartphone_videos(youtube_client, query, max_results=5):
    print(f"[*] Đang tìm kiếm {max_results} video cho từ khóa: '{query}'...")
    request = youtube_client.search().list(
        q=query,
        part='snippet',
        type='video',
        maxResults=max_results
    )
    response = request.execute()
    
    videos = []
    for item in response.get('items', []):
        videos.append({
            'video_id': item['id']['videoId'],
            'title': item['snippet']['title'],
            'channel_title': item['snippet']['channelTitle'],
            'publish_date': item['snippet']['publishedAt']
        })
    return videos

def get_video_stats(youtube_client, video_id):
    """Lấy lượng tương tác (views, likes, comments) của video"""
    request = youtube_client.videos().list(
        part='statistics',
        id=video_id
    )
    response = request.execute()
    
    if not response.get('items'):
        return None
        
    stats = response['items'][0]['statistics']
    return {
        'view_count': int(stats.get('viewCount', 0)),
        'like_count': int(stats.get('likeCount', 0)),
        'comment_count': int(stats.get('commentCount', 0))
    }

def get_video_comments(youtube_client, video_id, max_comments=50):
    """Lấy bình luận để phục vụ Sentiment Analysis và Topic Modeling"""
    comments = []
    try:
        request = youtube_client.commentThreads().list(
            part='snippet',
            videoId=video_id,
            maxResults=max_comments,
            textFormat='plainText'
        )
        response = request.execute()
        
        for item in response.get('items', []):
            comment = item['snippet']['topLevelComment']['snippet']
            comments.append({
                'video_id': video_id,
                'author': comment['authorDisplayName'],
                'text': comment['textDisplay'],
                'like_count': int(comment.get('likeCount', 0)),
                'published_at': comment['publishedAt']
            })
    except Exception as e:
        print(f"[-] Bỏ qua bình luận video {video_id} (Có thể video tắt bình luận hoặc bị giới hạn). Lỗi: {e}")
        
    return comments

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


if __name__ == "__main__":
    try:
        config = load_credentials()

        API_KEY = config.get('YOUTUBE_API_KEY')

        if not API_KEY or API_KEY.startswith("AIzaSyYourActualAPIKey"):
            raise ValueError("API Key chưa được cấu hình chính xác trong file JSON.")

        youtube = build('youtube', 'v3', developerKey=API_KEY)

        print(
            "[THÀNH CÔNG] Đã cấu hình YouTube API Client thành công!\n"
            + "-" * 50
        )

        SEARCH_QUERIES = [
            "đánh giá VF3",
            "đánh giá VF6",
            "đánh giá VF8",
            "đánh giá VF9",
            "đánh giá VF7",
            "đánh giá VF5",
            "đánh giá VF e34",
            "đánh giá Wuling Bingo 2026",
            "đánh giá Geely EX2 2026",
            "đánh giá VinFast Herio Green 2026",
            "đánh giá BYD Dolphin 2026",
            "đánh giá BYD M6 2026",
        ]

        for query in SEARCH_QUERIES:

            SEARCH_QUERY = query
            MAX_VIDEOS = 50
            MAX_COMMENTS = 2000

            print(f"\n{'=' * 70}")
            print(f"ĐANG XỬ LÝ TỪ KHÓA: {SEARCH_QUERY}")
            print(f"{'=' * 70}")

            videos_list = search_smartphone_videos(
                youtube,
                SEARCH_QUERY,
                max_results=MAX_VIDEOS
            )

            all_video_data = []
            all_comments_data = []

            for i, vid in enumerate(videos_list, start=1):

                vid_id = vid['video_id']

                print(
                    f"[{i}/{len(videos_list)}] "
                    f"Đang xử lý video ID: {vid_id}"
                )

                stats = get_video_stats(youtube, vid_id)

                if stats:
                    vid.update(stats)
                    all_video_data.append(vid)

                comments = get_video_comments(
                    youtube,
                    vid_id,
                    max_comments=MAX_COMMENTS
                )

                all_comments_data.extend(comments)

                time.sleep(1)

            df_videos = pd.DataFrame(all_video_data)
            df_comments = pd.DataFrame(all_comments_data)

            youtube_video_file = (
                f"youtube_video_stats_{SEARCH_QUERY}.csv"
                .replace(" ", "_")
            )

            youtube_comment_file = (
                f"youtube_comments_{SEARCH_QUERY}.csv"
                .replace(" ", "_")
            )

            df_videos.to_csv(
                youtube_video_file,
                index=False,
                encoding='utf-8-sig'
            )

            df_comments.to_csv(
                youtube_comment_file,
                index=False,
                encoding='utf-8-sig'
            )

            print(
                f"[YOUTUBE] Đã lưu {len(df_videos)} video vào "
                f"{youtube_video_file}"
            )

            print(
                f"[YOUTUBE] Đã lưu {len(df_comments)} bình luận vào "
                f"{youtube_comment_file}"
            )

            print("\n[REDDIT] Bắt đầu thu thập dữ liệu...")

            df_reddit = crawl_reddit_comments(SEARCH_QUERY)

            if df_reddit is not None and not df_reddit.empty:

                reddit_file = (
                    f"reddit_comments_{SEARCH_QUERY}.csv"
                    .replace(" ", "_")
                )

                df_reddit.to_csv(
                    reddit_file,
                    index=False,
                    encoding="utf-8-sig"
                )

                print(
                    f"[REDDIT] Đã lưu {len(df_reddit)} bản ghi vào "
                    f"{reddit_file}"
                )

            print("\n[FACEBOOK] Bắt đầu thu thập dữ liệu...")

            if (
                FACEBOOK_ACCESS_TOKEN
                and FACEBOOK_ACCESS_TOKEN != "YOUR_FACEBOOK_ACCESS_TOKEN"
            ):

                df_fb = crawl_facebook_comments(
                    SEARCH_QUERY,
                    FACEBOOK_ACCESS_TOKEN
                )

                if df_fb is not None and not df_fb.empty:

                    fb_file = (
                        f"facebook_comments_{SEARCH_QUERY}.csv"
                        .replace(" ", "_")
                    )

                    df_fb.to_csv(
                        fb_file,
                        index=False,
                        encoding="utf-8-sig"
                    )

                    print(
                        f"[FACEBOOK] Đã lưu {len(df_fb)} bản ghi vào "
                        f"{fb_file}"
                    )

        print("\n[HOÀN TẤT] Đã xử lý xong toàn bộ dữ liệu.")

    except FileNotFoundError as fnf_error:
        print(f"[LỖI FILE] {fnf_error}")

    except ValueError as val_error:
        print(f"[LỖI CẤU HÌNH] {val_error}")

    except Exception as e:
        print(f"[LỖI HỆ THỐNG] {e}")