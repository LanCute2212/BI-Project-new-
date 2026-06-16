import os
import sys
import pandas as pd
import streamlit as st
import plotly.express as px
from collections import Counter

current_dir = os.path.dirname(os.path.abspath(__file__))
if "phase_" in os.path.basename(current_dir).lower() or "phase_" in current_dir.lower():
    BASE_DIR = os.path.abspath(os.path.join(current_dir, ".."))
else:
    BASE_DIR = current_dir

sys.path.append(os.path.join(BASE_DIR, "phase_2_preprocess"))
sys.path.append(os.path.join(BASE_DIR, "phase_3_modeling"))
from preprocess import preprocess_vietnamese_text
from sentiment_model import run_phobert_sentiment, extract_car_model, extract_aspect

st.set_page_config(
    page_title="VinFast BI Sentiment Dashboard",
    page_icon="⚡",
    layout="wide"
)

st.sidebar.header("💾 Cấu hình Cơ sở dữ liệu")
db_type = st.sidebar.selectbox("Loại Database", ["SQLite (Offline)", "MySQL (Online)"], index=0)

if db_type == "MySQL (Online)":
    mysql_host = st.sidebar.text_input("MySQL Host", "localhost", help="Địa chỉ IP hoặc localhost của MySQL server")
    mysql_port = st.sidebar.number_input("MySQL Port", value=3306, step=1)
    mysql_user = st.sidebar.text_input("MySQL User", "root")
    mysql_pass = st.sidebar.text_input("MySQL Password", "", type="password")
    mysql_db = st.sidebar.text_input("MySQL Database", "sentiment_dwh")

def load_data_from_db():
    query = """
    SELECT 
        f.comment_key,
        f.comment_text,
        f.like_count,
        d.full_date,
        d.month,
        d.year,
        s.channel_name,
        s.platform,
        sen.sentiment_label,
        sen.confidence_score,
        m.model_name,
        m.brand,
        a.aspect_name,
        u.username as author,
        u.author_type,
        u.follower_count
    FROM fact_comments f
    JOIN dim_date d ON f.date_key = d.date_key
    JOIN dim_source s ON f.source_key = s.source_key
    JOIN dim_sentiment sen ON f.sentiment_key = sen.sentiment_key
    JOIN dim_car_model m ON f.model_key = m.model_key
    JOIN dim_aspect a ON f.aspect_key = a.aspect_key
    JOIN dim_user u ON f.user_key = u.user_key
    """
    if db_type == "MySQL (Online)":
        try:
            import pymysql
            conn = pymysql.connect(
                host=mysql_host,
                port=int(mysql_port),
                user=mysql_user,
                password=mysql_pass,
                database=mysql_db,
                charset='utf8mb4'
            )
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.sidebar.error(f"❌ Không kết nối được MySQL: {e}")
            return None
    else:
        try:
            import sqlite3
            db_file_path = os.path.join(BASE_DIR, "data", "sentiment_dwh.db")
            conn = sqlite3.connect(db_file_path)
            df = pd.read_sql_query(query, conn)
            conn.close()
            return df
        except Exception as e:
            st.sidebar.error(f"❌ Không kết nối được SQLite: {e}")
            return None

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    .main {
        background-color: #f4f6fa;
    }
    
    h1, h2, h3, h4, h5, h6 {
        color: #00529C !important;
        font-weight: 700 !important;
    }
    
    /* Cấu hình lại các ô Metric */
    .stMetric {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 6px 16px rgba(0, 82, 156, 0.08);
        border-top: 4px solid #00529C;
        transition: transform 0.2s ease;
    }
    .stMetric:hover {
        transform: translateY(-2px);
    }
    
    /* Styling Sidebar để dễ đọc hơn */
    section[data-testid="stSidebar"] {
        background-color: #0b1a30 !important;
    }
    
    section[data-testid="stSidebar"] label {
        color: #e2e8f0 !important;
        font-weight: 600 !important;
        font-size: 0.95rem !important;
    }
    
    section[data-testid="stSidebar"] h1, 
    section[data-testid="stSidebar"] h2, 
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] h4,
    section[data-testid="stSidebar"] h5,
    section[data-testid="stSidebar"] h6,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] p {
        color: #ffffff !important;
    }
    
    section[data-testid="stSidebar"] hr {
        border-color: #1e2d4a !important;
    }
    
    /* Đảm bảo dropdown options hiển thị chữ đen rõ ràng */
    section[data-testid="stSidebar"] div[data-baseweb="select"] {
        color: #0b1a30 !important;
    }
    
    /* Fix cho các nhãn slider */
    section[data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p {
        color: #e2e8f0 !important;
    }

    /* Bo tròn và bóng đổ cho biểu đồ */
    .chart-container {
        background-color: white;
        padding: 24px;
        border-radius: 16px;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.04);
        margin-bottom: 24px;
        border: 1px solid #eef2f6;
    }
</style>
""", unsafe_allow_html=True)

# --- PHẦN GIAO DIỆN CHÍNH ---
st.markdown("<h1 style='text-align: center; margin-bottom: 20px;'>⚡ VinFast Brand Sentiment BI Dashboard 📊</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #555555; font-size: 1.1rem;'>Hệ thống Social Listening phân tích ý kiến khách hàng về xe điện VinFast tích hợp PhoBERT & Star Schema DWH</p>", unsafe_allow_html=True)
st.markdown("---")

df = load_data_from_db()

# Bản đồ màu sắc cảm xúc chuẩn hóa
color_map = {'Tích cực': '#28a745', 'Tiêu cực': '#dc3545', 'Trung lập': '#6c757d'}

if df is None or len(df) == 0:
    st.warning("⚠️ Hiện tại chưa kết nối được MySQL/SQLite hoặc chưa có dữ liệu trong Kho dữ liệu (Data Warehouse).")
    st.info("👉 Vui lòng chạy file pipeline `sentiment_model.py` để sinh dữ liệu và nạp cơ sở dữ liệu.")
    st.code("py sentiment_model.py", language="bash")
else:
    st.sidebar.markdown("### 🔎 Bộ Lọc Báo Cáo")
    
    brands = sorted(df['brand'].unique().tolist())
    selected_brands = st.sidebar.multiselect("Thương hiệu:", brands, default=brands)
    
    available_models = sorted(df[df['brand'].isin(selected_brands)]['model_name'].unique().tolist())
    selected_models = st.sidebar.multiselect("Dòng xe:", available_models, default=available_models)
    
    aspects = sorted(df['aspect_name'].unique().tolist())
    selected_aspects = st.sidebar.multiselect("Khía cạnh:", aspects, default=aspects)
    
    platforms = sorted(df['platform'].unique().tolist())
    selected_platforms = st.sidebar.multiselect("Nguồn dữ liệu:", platforms, default=platforms)
    
    sentiments = sorted(df['sentiment_label'].unique().tolist())
    selected_sentiments = st.sidebar.multiselect("Cảm xúc:", sentiments, default=sentiments)
    
    author_types = df['author_type'].unique().tolist()
    selected_author_types = st.sidebar.multiselect("Nhóm Tác giả:", author_types, default=author_types)
    
    max_f = int(df['follower_count'].max())
    min_followers, max_followers = st.sidebar.slider(
        "Lượng Followers của tác giả:", 
        0, max_f, (0, max_f), 
        step=max(1, max_f // 100)
    )
    
    filtered_df = df[
        df['brand'].isin(selected_brands) &
        df['model_name'].isin(selected_models) &
        df['aspect_name'].isin(selected_aspects) &
        df['platform'].isin(selected_platforms) &
        df['sentiment_label'].isin(selected_sentiments) &
        df['author_type'].isin(selected_author_types) &
        (df['follower_count'] >= min_followers) &
        (df['follower_count'] <= max_followers)
    ]
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📤 Xuất Dữ Liệu Cho BI Tool")
    
    export_format = st.sidebar.selectbox(
        "Định dạng xuất dữ liệu:",
        ["Flat Table (Khuyên dùng)", "Star Schema (Dim & Fact)"],
        help="Flat Table phù hợp để kéo thả nhanh trên Tableau. Star Schema xuất riêng lẻ các bảng để dựng quan hệ trên Power BI."
    )
    
    if export_format == "Flat Table (Khuyên dùng)":
        flat_csv = filtered_df.to_csv(index=False, encoding="utf-8-sig")
        st.sidebar.download_button(
            label="📥 Tải Bảng Phẳng CSV",
            data=flat_csv,
            file_name="vinfast_sentiment_flat.csv",
            mime="text/csv"
        )
    else:
        st.sidebar.info("Tải xuống từng bảng dưới đây để Import vào Power BI/Tableau:")
        
        dim_date_df = filtered_df[['full_date', 'month', 'year']].drop_duplicates()
        dim_date_df['date_key'] = pd.to_datetime(dim_date_df['full_date']).dt.strftime('%Y%m%d')
        dim_date_df['day'] = pd.to_datetime(dim_date_df['full_date']).dt.day
        dim_date_df['quarter'] = (pd.to_datetime(dim_date_df['full_date']).dt.month - 1) // 3 + 1
        dim_date_csv = dim_date_df[['date_key', 'full_date', 'day', 'month', 'year', 'quarter']].to_csv(index=False, encoding="utf-8-sig")
        
        dim_source_df = filtered_df[['channel_name', 'platform']].drop_duplicates()
        dim_source_df['source_key'] = "src_" + dim_source_df['platform'].str.lower().str.replace(" ", "_") + "_" + dim_source_df['channel_name'].str.lower().str.replace(" ", "_").str.replace("đ", "d").str.replace("/", "_").str.replace("[", "").str.replace("]", "")
        dim_source_csv = dim_source_df[['source_key', 'channel_name', 'platform']].to_csv(index=False, encoding="utf-8-sig")
        
        dim_user_df = filtered_df[['author', 'author_type', 'follower_count']].drop_duplicates()
        dim_user_df['user_key'] = "usr_" + dim_user_df['author'].apply(lambda x: str(hash(str(x)) % 100000000))
        dim_user_df.columns = ['username', 'author_type', 'follower_count', 'user_key']
        dim_user_csv = dim_user_df[['user_key', 'username', 'author_type', 'follower_count']].to_csv(index=False, encoding="utf-8-sig")
        
        dim_model_df = filtered_df[['model_name', 'brand']].drop_duplicates()
        model_map = {
            'VF 3': ('model_vf3', 'Mini-SUV'), 'VF 5': ('model_vf5', 'A-SUV'),
            'VF e34': ('model_vfe34', 'C-SUV'), 'VF 6': ('model_vf6', 'B-SUV'),
            'VF 7': ('model_vf7', 'C-SUV'), 'VF 8': ('model_vf8', 'D-SUV'),
            'VF 9': ('model_vf9', 'E-SUV'), 'Atto 3': ('model_byd_atto3', 'C-SUV'),
            'Mini EV': ('model_wuling_mini', 'Micro-car'), 'SU7': ('model_xiaomi_su7', 'Sedan')
        }
        dim_model_df['model_key'] = dim_model_df['model_name'].apply(lambda x: model_map.get(x, ('model_other', 'Khác'))[0])
        dim_model_df['segment'] = dim_model_df['model_name'].apply(lambda x: model_map.get(x, ('model_other', 'Khác'))[1])
        dim_model_csv = dim_model_df[['model_key', 'model_name', 'brand', 'segment']].to_csv(index=False, encoding="utf-8-sig")
        
        dim_aspect_df = filtered_df[['aspect_name']].drop_duplicates()
        aspect_map = {
            'Trạm sạc': ('asp_charging', 'Số lượng, phân bố, tốc độ sạc, sự tiện lợi của hệ thống trạm sạc'),
            'Pin & Thuê pin': ('asp_battery', 'Chính sách thuê pin, dung lượng pin, chai pin, sạc tại nhà'),
            'Phần mềm & Lỗi vặt': ('asp_software', 'Lỗi phần mềm, treo màn hình, ADAS, lỗi ảo, cập nhật firmware'),
            'Vận hành & Tiện nghi': ('asp_comfort', 'Động cơ, cảm giác lái, cách âm, điều hòa, độ êm ái, nội thất'),
            'Dịch vụ & Hậu mãi': ('asp_service', 'Chính sách bảo hành, dịch vụ cứu hộ, thái độ showroom, phụ tùng thay thế'),
            'Giá bán & Khuyến mãi': ('asp_price', 'Giá xe, chương trình ưu đãi, thuế trước bạ, chi phí vận hành so với xe xăng')
        }
        dim_aspect_df['aspect_key'] = dim_aspect_df['aspect_name'].apply(lambda x: aspect_map.get(x, ('asp_other', 'Khác'))[0])
        dim_aspect_df['description'] = dim_aspect_df['aspect_name'].apply(lambda x: aspect_map.get(x, ('asp_other', 'Khác'))[1])
        dim_aspect_csv = dim_aspect_df[['aspect_key', 'aspect_name', 'description']].to_csv(index=False, encoding="utf-8-sig")

        fact_df = filtered_df.copy()
        fact_df['date_key'] = pd.to_datetime(fact_df['full_date']).dt.strftime('%Y%m%d')
        fact_df['source_key'] = "src_" + fact_df['platform'].str.lower().str.replace(" ", "_") + "_" + fact_df['channel_name'].str.lower().str.replace(" ", "_").str.replace("đ", "d").str.replace("/", "_").str.replace("[", "").str.replace("]", "")
        fact_df['user_key'] = "usr_" + fact_df['author'].apply(lambda x: str(hash(str(x)) % 100000000))
        fact_df['model_key'] = fact_df['model_name'].apply(lambda x: model_map.get(x, ('model_other', 'Khác'))[0])
        fact_df['aspect_key'] = fact_df['aspect_name'].apply(lambda x: aspect_map.get(x, ('asp_other', 'Khác'))[0])
        fact_df['sentiment_key'] = fact_df['comment_key'].apply(lambda x: f"sent_{x}")
        
        dim_sentiment_df = filtered_df[['comment_key', 'sentiment_label', 'confidence_score']].copy()
        dim_sentiment_df['sentiment_key'] = dim_sentiment_df['comment_key'].apply(lambda x: f"sent_{x}")
        dim_sentiment_csv = dim_sentiment_df[['sentiment_key', 'sentiment_label', 'confidence_score']].to_csv(index=False, encoding="utf-8-sig")
        
        fact_csv = fact_df[['comment_key', 'date_key', 'source_key', 'sentiment_key', 'model_key', 'aspect_key', 'user_key', 'comment_text', 'like_count']].to_csv(index=False, encoding="utf-8-sig")
        
        st.sidebar.download_button("📥 Tải Fact_Comments.csv", fact_csv, "fact_comments.csv", "text/csv")
        st.sidebar.download_button("📥 Tải Dim_User.csv", dim_user_csv, "dim_user.csv", "text/csv")
        st.sidebar.download_button("📥 Tải Dim_Source.csv", dim_source_csv, "dim_source.csv", "text/csv")
        st.sidebar.download_button("📥 Tải Dim_Date.csv", dim_date_csv, "dim_date.csv", "text/csv")
        st.sidebar.download_button("📥 Tải Dim_Sentiment.csv", dim_sentiment_csv, "dim_sentiment.csv", "text/csv")
        st.sidebar.download_button("📥 Tải Dim_Car_Model.csv", dim_model_csv, "dim_car_model.csv", "text/csv")
        st.sidebar.download_button("📥 Tải Dim_Aspect.csv", dim_aspect_csv, "dim_aspect.csv", "text/csv")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Tổng bình luận phân tích", f"{len(filtered_df):,}")
    with col2:
        pos_ratio = len(filtered_df[filtered_df['sentiment_label'] == 'Tích cực']) / max(1, len(filtered_df)) * 100
        st.metric("Tỷ lệ Tích Cực", f"{pos_ratio:.1f}%")
    with col3:
        total_reach = filtered_df['follower_count'].sum()
        st.metric("Tổng lượt tiếp cận (Reach)", f"{total_reach:,}")
    with col4:
        total_likes = filtered_df['like_count'].sum()
        st.metric("Tổng lượt tương tác (Like)", f"{int(total_likes):,}")
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_left, col_right = st.columns(2)
    
    with col_left:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("📈 Phân Phối Cảm Xúc Toàn Cục")
        sentiment_counts = filtered_df['sentiment_label'].value_counts().reset_index()
        sentiment_counts.columns = ['Cảm xúc', 'Số lượng']
        
        fig_pie = px.pie(
            sentiment_counts, 
            values='Số lượng', 
            names='Cảm xúc', 
            color='Cảm xúc',
            color_discrete_map=color_map,
            hole=0.4
        )
        fig_pie.update_traces(textinfo='percent+label')
        fig_pie.update_layout(margin=dict(t=30, b=10, l=10, r=10))
        st.plotly_chart(fig_pie, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_right:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("📅 Xu Hướng Cảm Xúc Theo Thời Gian")
        trend_df = filtered_df.groupby(['full_date', 'sentiment_label']).size().reset_index(name='Số lượng')
        
        fig_line = px.line(
            trend_df, 
            x='full_date', 
            y='Số lượng', 
            color='sentiment_label',
            color_discrete_map=color_map,
            labels={'full_date': 'Ngày', 'Số lượng': 'Số lượng bình luận', 'sentiment_label': 'Cảm xúc'},
            markers=True
        )
        fig_line.update_layout(
            xaxis_title="Ngày", 
            yaxis_title="Số bình luận",
            margin=dict(t=30, b=10, l=10, r=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        st.plotly_chart(fig_line, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    col_model, col_aspect = st.columns(2)
    
    with col_model:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("🚗 Cảm Xúc Khách Hàng Theo Từng Dòng Xe")
        if not filtered_df.empty:
            model_sent = filtered_df.groupby(['model_name', 'sentiment_label']).size().reset_index(name='Số lượng')
            fig_model = px.bar(
                model_sent,
                x='Số lượng',
                y='model_name',
                color='sentiment_label',
                orientation='h',
                color_discrete_map=color_map,
                labels={'model_name': 'Dòng xe', 'sentiment_label': 'Cảm xúc'}
            )
            fig_model.update_layout(
                yaxis={'categoryorder':'total ascending'},
                margin=dict(t=30, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_model, use_container_width=True)
        else:
            st.write("Không có dữ liệu dòng xe.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_aspect:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("💡 Cảm Xúc Khách Hàng Theo Khía Cạnh Phản Hồi")
        if not filtered_df.empty:
            aspect_sent = filtered_df.groupby(['aspect_name', 'sentiment_label']).size().reset_index(name='Số lượng')
            fig_aspect = px.bar(
                aspect_sent,
                x='Số lượng',
                y='aspect_name',
                color='sentiment_label',
                orientation='h',
                color_discrete_map=color_map,
                labels={'aspect_name': 'Khía cạnh', 'sentiment_label': 'Cảm xúc'}
            )
            fig_aspect.update_layout(
                yaxis={'categoryorder':'total ascending'},
                margin=dict(t=30, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_aspect, use_container_width=True)
        else:
            st.write("Không có dữ liệu khía cạnh.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    col_usr_sent, col_reach_brand = st.columns(2)
    
    with col_usr_sent:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("👥 So Sánh Cảm Xúc: Celebs/KOLs vs Người Dùng Thường")
        if not filtered_df.empty:
            user_sent = filtered_df.groupby(['author_type', 'sentiment_label']).size().reset_index(name='Số lượng')
            fig_user_sent = px.bar(
                user_sent,
                x='author_type',
                y='Số lượng',
                color='sentiment_label',
                barmode='group',
                color_discrete_map=color_map,
                labels={'author_type': 'Nhóm tác giả', 'Số lượng': 'Số bình luận', 'sentiment_label': 'Cảm xúc'}
            )
            fig_user_sent.update_layout(
                margin=dict(t=30, b=10, l=10, r=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_user_sent, use_container_width=True)
        else:
            st.write("Không có dữ liệu tác giả.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_reach_brand:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("📢 Tổng Lượng Tiếp Cận (Reach) Theo Hãng Xe")
        if not filtered_df.empty:
            reach_brand = filtered_df.groupby('brand')['follower_count'].sum().reset_index()
            fig_reach = px.bar(
                reach_brand,
                x='follower_count',
                y='brand',
                orientation='h',
                color_discrete_sequence=['#00529C'],
                labels={'follower_count': 'Tổng Followers (Reach)', 'brand': 'Hãng xe'}
            )
            fig_reach.update_layout(
                yaxis={'categoryorder':'total ascending'},
                margin=dict(t=30, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_reach, use_container_width=True)
        else:
            st.write("Không có dữ liệu thương hiệu.")
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_tbl, col_words = st.columns([3, 2])
    
    with col_tbl:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("💬 Danh Sách Ý Kiến Gần Đây")
        display_cols = ['full_date', 'author', 'author_type', 'follower_count', 'comment_text', 'model_name', 'aspect_name', 'sentiment_label', 'like_count']
        temp_show_df = filtered_df[display_cols].sort_values(by='like_count', ascending=False).head(10)
        temp_show_df.columns = ['Ngày', 'Tác giả', 'Nhóm', 'Followers', 'Bình luận', 'Dòng xe', 'Khía cạnh', 'Cảm xúc', 'Số Like']
        st.dataframe(temp_show_df, use_container_width=True, hide_index=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_words:
        st.markdown("<div class='chart-container'>", unsafe_allow_html=True)
        st.subheader("🔤 Từ Khóa Xuất Hiện Nhiều Nhất")
        all_words = []
        for text in filtered_df['comment_text']:
            words = preprocess_vietnamese_text(text, tokenize=False).split()
            stop_words = ["xe", "điện", "có", "là", "và", "của", "cho", "được", "bị", "này", "với", "nhưng", "một", "về", "cái", "cho", "nhiều", "vinfast"]
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
                color_discrete_sequence=['#00529C']
            )
            fig_bar.update_layout(
                yaxis={'categoryorder':'total ascending'},
                margin=dict(t=10, b=10, l=10, r=10)
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.write("Không đủ dữ liệu từ khóa.")
        st.markdown("</div>", unsafe_allow_html=True)

st.markdown("---")

st.subheader("🔮 Trải Nghiệm Dự Đoán Cảm Xúc Bằng Mô Hình (Real-time Prediction)")
user_input = st.text_area("Nhập một bình luận tiếng Việt về xe điện để kiểm tra cảm xúc:", placeholder="Ví dụ: Xe VF 8 đi phượt đầm chắc cực sướng, cơ mà phần mềm hay báo lỗi hệ thống ảo...")

if st.button("Phân tích bình luận"):
    if user_input.strip() == "":
        st.warning("Vui lòng nhập nội dung bình luận!")
    else:
        with st.spinner("Đang chạy mô hình phân tích cảm xúc & trích xuất thông tin..."):
            result = run_phobert_sentiment([user_input])[0]
            sentiment_pred, score = result
            
            extracted_model_key = extract_car_model(user_input)
            extracted_aspect_key = extract_aspect(user_input)
            
            model_map = {
                'model_vf3': 'VF 3', 'model_vf5': 'VF 5', 'model_vfe34': 'VF e34',
                'model_vf6': 'VF 6', 'model_vf7': 'VF 7', 'model_vf8': 'VF 8',
                'model_vf9': 'VF 9', 'model_byd_atto3': 'BYD Atto 3',
                'model_wuling_mini': 'Wuling Mini EV', 'model_xiaomi_su7': 'Xiaomi SU7',
                'model_other': 'Khác/Chung'
            }
            aspect_map = {
                'asp_charging': 'Trạm sạc', 'asp_battery': 'Pin & Thuê pin',
                'asp_software': 'Phần mềm & Lỗi vặt', 'asp_comfort': 'Vận hành & Tiện nghi',
                'asp_service': 'Dịch vụ & Hậu mãi', 'asp_price': 'Giá bán & Khuyến mãi',
                'asp_other': 'Khác'
            }
            
            model_display = model_map.get(extracted_model_key, "Khác/Chung")
            aspect_display = aspect_map.get(extracted_aspect_key, "Khác")
            
            if sentiment_pred == "Tích cực":
                st.success(f"🟢 **Cảm xúc: Tích cực** (Độ tin cậy: {score*100:.2f}%)")
            elif sentiment_pred == "Tiêu cực":
                st.error(f"🔴 **Cảm xúc: Tiêu cực** (Độ tin cậy: {score*100:.2f}%)")
            else:
                st.info(f"🔵 **Cảm xúc: Trung lập** (Độ tin cậy: {score*100:.2f}%)")
                
            st.markdown(f"👉 **Dòng xe nhận diện:** `{model_display}`")
            st.markdown(f"👉 **Khía cạnh phản hồi:** `{aspect_display}`")
            
            segmented = preprocess_vietnamese_text(user_input, tokenize=True)
            st.markdown(f"**Kết quả tách từ tiếng Việt để đưa vào PhoBERT:** `{segmented}`")
