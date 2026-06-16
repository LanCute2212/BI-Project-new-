import os
import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from collections import Counter
from phase_2_preprocess.preprocess import preprocess_vietnamese_text
from sentiment_model import run_phobert_sentiment

# Đặt tiêu đề và cấu hình trang
st.set_page_config(
    page_title="VinaSmart BI Dashboard - Social Media Sentiment",
    page_icon="📊",
    layout="wide"
)

# Đường dẫn tệp tin
DB_PATH = os.path.join("data", "sentiment_dwh.db")

# Hàm kết nối CSDL và đọc dữ liệu
def load_data_from_db():
    if not os.path.exists(DB_PATH):
        return None, None, None
        
    conn = sqlite3.connect(DB_PATH)
    
    # 1. Đọc dữ liệu Fact kết hợp với các Dimension
    query = """
    SELECT 
        f.comment_key,
        f.author,
        f.comment_text,
        f.like_count,
        d.full_date,
        d.month,
        d.year,
        s.channel_name,
        s.platform,
        sen.sentiment_label,
        sen.confidence_score
    FROM fact_comments f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_source s ON f.source_key = s.source_key
    JOIN dim_sentiment sen ON f.sentiment_key = sen.sentiment_key
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

# CSS tùy chỉnh để làm dashboard trông đẹp mắt hơn
st.markdown("""
<style>
    .main {
        background-color: #f8f9fa;
    }
    h1 {
        color: #1e3d59;
        font-family: 'Outfit', sans-serif;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #17a2b8;
    }
    .css-1r6g72q {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
</style>
""", unsafe_style = True)

# --- PHẦN GIAO DIỆN CHÍNH ---
st.title("📊 Phân Tích Cảm Xúc & Phản Hồi Về Xe Điện Tại Việt Nam")
st.markdown("Hệ thống tích hợp mô hình **PhoBERT** và kiến trúc Kho dữ liệu hình sao (Star Schema).")

df = load_data_from_db()

if df is None or len(df) == 0:
    st.warning("⚠️ Hiện tại chưa có dữ liệu trong Kho dữ liệu (Data Warehouse).")
    st.info("👉 Vui lòng chạy file `sentiment_model.py` trước để thu thập, gán nhãn cảm xúc bằng PhoBERT và đẩy dữ liệu vào CSDL.")
    st.code("python sentiment_model.py", language="bash")
else:
    # Sidebar lọc dữ liệu
    st.sidebar.header("Bộ Lọc Dữ Liệu")
    
    # Lọc theo nguồn
    sources = df['channel_name'].unique().tolist()
    selected_sources = st.sidebar.multiselect("Nguồn dữ liệu:", sources, default=sources)
    
    # Lọc theo cảm xúc
    sentiments = df['sentiment_label'].unique().tolist()
    selected_sentiments = st.sidebar.multiselect("Cảm xúc:", sentiments, default=sentiments)
    
    # Áp dụng bộ lọc
    filtered_df = df[
        df['channel_name'].isin(selected_sources) & 
        df['sentiment_label'].isin(selected_sentiments)
    ]
    
    # --- ROW 1: METRICS ---
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng bình luận phân tích", len(filtered_df))
    with col2:
        pos_ratio = len(filtered_df[filtered_df['sentiment_label'] == 'Tích cực']) / max(1, len(filtered_df)) * 100
        st.metric("Tỷ lệ Tích Cực", f"{pos_ratio:.1f}%")
    with col3:
        avg_confidence = filtered_df['confidence_score'].mean() * 100
        st.metric("Độ tin cậy trung bình", f"{avg_confidence:.1f}%")
    with col4:
        total_likes = filtered_df['like_count'].sum()
        st.metric("Tổng lượt tương tác (Like)", int(total_likes))
        
    st.markdown("---")
    
    # --- ROW 2: BIỂU ĐỒ TRỰC QUAN HÓA ---
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.subheader("📈 Phân Phối Cảm Xúc Ý Kiến Khách Hàng")
        sentiment_counts = filtered_df['sentiment_label'].value_counts().reset_index()
        sentiment_counts.columns = ['Cảm xúc', 'Số lượng']
        
        # Thiết lập màu sắc trực quan (Green cho Positive, Red cho Negative, Grey cho Neutral)
        color_map = {'Tích cực': '#28a745', 'Tiêu cực': '#dc3545', 'Trung lập': '#6c757d'}
        fig_pie = px.pie(
            sentiment_counts, 
            values='Số lượng', 
            names='Cảm xúc', 
            color='Cảm xúc',
            color_discrete_map=color_map,
            hole=0.4
        )
        fig_pie.update_traces(textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)
        
    with col_right:
        st.subheader("📅 Xu Hướng Cảm Xúc Theo Thời Gian")
        # Gom nhóm theo ngày và cảm xúc
        trend_df = filtered_df.groupby(['full_date', 'sentiment_label']).size().reset_index(name='count')
        
        fig_line = px.line(
            trend_df, 
            x='full_date', 
            y='count', 
            color='sentiment_label',
            color_discrete_map=color_map,
            labels={'full_date': 'Ngày', 'count': 'Số lượng bình luận', 'sentiment_label': 'Cảm xúc'},
            markers=True
        )
        fig_line.update_layout(xaxis_title="Ngày", yaxis_title="Số bình luận")
        st.plotly_chart(fig_line, use_container_width=True)
        
    st.markdown("---")
    
    # --- ROW 3: BÌNH LUẬN TIÊU BIỂU & TỪ KHÓA ---
    col_tbl, col_words = st.columns([3, 2])
    
    with col_tbl:
        st.subheader("💬 Danh Sách Ý Kiến Gần Đây")
        display_cols = ['full_date', 'author', 'comment_text', 'sentiment_label', 'like_count']
        temp_show_df = filtered_df[display_cols].sort_values(by='like_count', ascending=False).head(10)
        temp_show_df.columns = ['Ngày', 'Tác giả', 'Bình luận', 'Cảm xúc', 'Số Like']
        st.dataframe(temp_show_df, use_container_width=True)
        
    with col_words:
        st.subheader("🔤 Từ Khóa Xuất Hiện Nhiều Nhất")
        # Trích xuất từ khóa thô sau tiền xử lý để làm biểu đồ tần suất từ
        all_words = []
        for text in filtered_df['comment_text']:
            # Lấy các từ đã được tách từ (không token gạch dưới để hiển thị biểu đồ đẹp hơn)
            words = preprocess_vietnamese_text(text, tokenize=False).split()
            # Loại bỏ các từ dừng cơ bản
            stop_words = ["xe", "điện", "có", "là", "và", "của", "cho", "được", "bị", "này", "với", "nhưng", "một", "về", "cái", "cho", "nhiều"]
            filtered_words = [w for w in words if w not in stop_words and len(w) > 1]
            all_words.extend(filtered_words)
            
        word_counts = Counter(all_words).most_common(10)
        if word_counts:
            word_df = pd.DataFrame(word_counts, columns=['Từ khóa', 'Tần suất'])
            fig_bar = px.bar(
                word_df, 
                x='Tần suất', 
                y='Từ khóa', 
                orientation='h',
                color_discrete_sequence=['#17a2b8']
            )
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.write("Không đủ dữ liệu từ khóa.")

st.markdown("---")

# --- ROW 4: KHU VỰC THỬ NGHIỆM MÔ HÌNH REAL-TIME ---
st.subheader("🔮 Trải Nghiệm Dự Đoán Cảm Xúc Bằng Mô Hình (Real-time Prediction)")
user_input = st.text_area("Nhập một bình luận tiếng Việt về xe điện để kiểm tra cảm xúc:", placeholder="Ví dụ: Xe VF3 đi phố gọn nhẹ và tiện lợi thật sự, gia đình mình ai cũng thích...")

if st.button("Dự đoán cảm xúc"):
    if user_input.strip() == "":
        st.warning("Vui lòng nhập nội dung bình luận!")
    else:
        with st.spinner("Đang chạy mô hình phân tích..."):
            # Chạy thử dự đoán cho 1 câu
            result = run_phobert_sentiment([user_input])[0]
            sentiment_pred, score = result
            
            # Hiển thị kết quả tương ứng với màu sắc
            if sentiment_pred == "Tích cực":
                st.success(f"🟢 **Cảm xúc: Tích cực** (Độ tin cậy: {score*100:.2f}%)")
            elif sentiment_pred == "Tiêu cực":
                st.error(f"🔴 **Cảm xúc: Tiêu cực** (Độ tin cậy: {score*100:.2f}%)")
            else:
                st.info(f"🔵 **Cảm xúc: Trung lập** (Độ tin cậy: {score*100:.2f}%)")
                
            # Hiển thị kết quả sau khi tách từ (Word Segmentation)
            segmented = preprocess_vietnamese_text(user_input, tokenize=True)
            st.markdown(f"**Kết quả tách từ tiếng Việt để đưa vào PhoBERT:** `{segmented}`")
