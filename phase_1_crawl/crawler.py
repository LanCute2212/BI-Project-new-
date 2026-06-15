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
    """Tìm kiếm video liên quan đến điện thoại và lấy Video ID"""
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


if __name__ == "__main__":
    try:
        config = load_credentials()
        
        API_KEY = config.get('YOUTUBE_API_KEY')
        
        if not API_KEY or API_KEY.startswith("AIzaSyYourActualAPIKey"):
            raise ValueError("API Key chưa được cấu hình chính xác trong file JSON.")

        youtube = build('youtube', 'v3', developerKey=API_KEY)
        print("[THÀNH CÔNG] Đã cấu hình YouTube API Client thành công!\n" + "-"*50)
        
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
            
            videos_list = search_smartphone_videos(youtube, SEARCH_QUERY, max_results=MAX_VIDEOS)
            
            all_video_data = []
            all_comments_data = []
            
            for i, vid in enumerate(videos_list, start=1):
                vid_id = vid['video_id']
                print(f"[{i}/{len(videos_list)}] Đang xử lý video ID: {vid_id}")
                
                stats = get_video_stats(youtube, vid_id)
                if stats:
                    vid.update(stats)
                    all_video_data.append(vid)
                    
                comments = get_video_comments(youtube, vid_id, max_comments=MAX_COMMENTS)
                all_comments_data.extend(comments)
                
                time.sleep(1) 

            print("-" * 50 + "\n[*] Đang lưu dữ liệu ra file CSV...")
            
            df_videos = pd.DataFrame(all_video_data)
            df_comments = pd.DataFrame(all_comments_data)
            
            df_videos.to_csv('youtube_video_stats.csv', index=False, encoding='utf-8-sig')
            df_comments.to_csv('youtube_comments.csv', index=False, encoding='utf-8-sig')
            
            print(f"[THÀNH CÔNG] Thu thập hoàn tất!")
            print(f" -> Đã lưu {len(df_videos)} video vào 'youtube_video_stats.csv'")
            print(f" -> Đã lưu {len(df_comments)} bình luận vào 'youtube_comments.csv'")

    except FileNotFoundError as fnf_error:
        print(f"[LỖI FILE] {fnf_error}")
    except ValueError as val_error:
        print(f"[LỖI CẤU HÌNH] {val_error}")
    except Exception as e:
        print(f"[LỖI HỆ THỐNG] Đã xảy ra lỗi không xác định: {e}")