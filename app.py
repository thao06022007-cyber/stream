import streamlit as st
import pandas as pd
import openai
from pathlib import Path
import json

# ========================================
# STREAMLIT PAGE CONFIG
# ========================================
st.set_page_config(
    page_title="Oil Survey Data Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========================================
# CUSTOM CSS FOR BEAUTIFUL UI
# ========================================
st.markdown("""
<style>
    .main-title {
        font-size: 3em;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 30px;
    }
    .cluster-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 25px;
        border-radius: 10px;
        margin: 15px 0;
        color: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .cluster-title {
        font-size: 1.8em;
        font-weight: bold;
        margin-bottom: 15px;
        border-bottom: 2px solid rgba(255, 255, 255, 0.3);
        padding-bottom: 10px;
    }
    .summary-text {
        font-size: 1.1em;
        line-height: 1.6;
        margin-top: 10px;
    }
    .stats-box {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 8px;
        margin: 10px 0;
        border-left: 4px solid #667eea;
    }
    .loading-spinner {
        text-align: center;
        color: #667eea;
        font-size: 1.2em;
    }
</style>
""", unsafe_allow_html=True)

# ========================================
# SIDEBAR CONFIGURATION
# ========================================
st.sidebar.markdown("## ⚙️ Cấu Hình")

# OpenAI API Key input
api_key = st.sidebar.text_input(
    "🔑 Nhập OpenAI API Key:",
    type="password",
    help="Bạn có thể lấy API Key từ https://platform.openai.com/api-keys"
)

# Model selection
model_choice = st.sidebar.selectbox(
    "🤖 Chọn mô hình AI:",
    ["gpt-4", "gpt-3.5-turbo"],
    help="Chọn mô hình để tóm tắt dữ liệu"
)

# File uploader
uploaded_file = st.sidebar.file_uploader(
    "📁 Tải lên file Excel:",
    type=["xlsx", "xls"],
    help="File phải có cột 'Cluster'"
)

# ========================================
# MAIN INTERFACE
# ========================================
st.markdown('<div class="main-title">📊 Phân Tích Khảo Sát Dầu Khí Việt Nam</div>', 
            unsafe_allow_html=True)

# Check for API key
if not api_key:
    st.warning("⚠️ Vui lòng nhập OpenAI API Key trong thanh bên để bắt đầu!")
    st.stop()

# Check for file
if not uploaded_file:
    st.info("📤 Vui lòng tải lên file Excel 'ResultTestDataOilSurveyVN.xlsx' để bắt đầu phân tích.")
    st.stop()

# ========================================
# LOAD AND PROCESS DATA
# ========================================
try:
    df = pd.read_excel(uploaded_file)
    
    # Display data stats
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("📝 Tổng số bản ghi", len(df))
    with col2:
        st.metric("📌 Số cột", len(df.columns))
    with col3:
        if 'Cluster' in df.columns:
            st.metric("🔀 Số nhóm Cluster", df['Cluster'].nunique())
        else:
            st.error("❌ File không có cột 'Cluster'!")
            st.stop()
    
    # Display first few rows
    with st.expander("👁️ Xem dữ liệu mẫu"):
        st.dataframe(df.head(10), use_container_width=True)
    
    st.divider()
    
    # ========================================
    # PROCESS CLUSTERS
    # ========================================
    st.markdown("## 🔍 Kết Quả Phân Tích Theo Nhóm")
    
    clusters = df['Cluster'].unique()
    
    # Button to start analysis
    if st.button("🚀 Bắt Đầu Phân Tích", key="analyze_btn", use_container_width=True):
        
        # Set OpenAI API key
        openai.api_key = api_key
        
        # Store results
        results = {}
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for idx, cluster in enumerate(sorted(clusters)):
            cluster_data = df[df['Cluster'] == cluster]
            
            # Update progress
            status_text.text(f"⏳ Đang xử lý Cluster {cluster}...")
            progress_bar.progress((idx + 1) / len(clusters))
            
            try:
                # Prepare data summary for AI
                data_summary = cluster_data.to_string()
                
                # Create prompt for AI
                prompt = f"""
Phân tích dữ liệu khảo sát dầu khí từ Việt Nam cho nhóm Cluster '{cluster}':

{data_summary[:2000]}

Hãy tóm tắt ý nghĩa của khảo sát này bằng 3-4 đoạn, bao gồm:
1. Tính chất chính của nhóm này
2. Các đặc điểm nổi bật
3. Ý nghĩa thực tiễn
4. Khuyến nghị (nếu có)

Trả lời bằng tiếng Việt.
"""
                
                # Call OpenAI API
                response = openai.ChatCompletion.create(
                    model=model_choice,
                    messages=[
                        {"role": "system", "content": "Bạn là một chuyên gia phân tích dữ liệu địa chất và khảo sát dầu khí."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                
                summary = response['choices'][0]['message']['content']
                results[cluster] = summary
                
            except Exception as e:
                results[cluster] = f"❌ Lỗi: {str(e)}"
        
        progress_bar.empty()
        status_text.empty()
        
        # ========================================
        # DISPLAY RESULTS
        # ========================================
        st.success("✅ Phân tích hoàn tất!")
        st.divider()
        
        # Create tabs for each cluster
        tabs = st.tabs([f"Cluster {cluster}" for cluster in sorted(clusters)])
        
        for tab, cluster in zip(tabs, sorted(clusters)):
            with tab:
                cluster_data = df[df['Cluster'] == cluster]
                
                # Display cluster statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"📊 Số bản ghi: **{len(cluster_data)}**")
                with col2:
                    st.info(f"📈 Tỷ lệ: **{len(cluster_data)/len(df)*100:.1f}%**")
                with col3:
                    st.info(f"🏷️ Cluster ID: **{cluster}**")
                
                # Display AI summary in beautiful card
                st.markdown(f'<div class="cluster-card"><div class="cluster-title">Tóm tắt AI - Cluster {cluster}</div><div class="summary-text">{results[cluster]}</div></div>', 
                           unsafe_allow_html=True)
                
                # Display cluster data
                with st.expander("📋 Xem chi tiết dữ liệu"):
                    st.dataframe(cluster_data, use_container_width=True)
        
        # ========================================
        # EXPORT RESULTS
        # ========================================
        st.divider()
        st.markdown("## 📥 Xuất Kết Quả")
        
        # Export as JSON
        json_results = json.dumps(results, ensure_ascii=False, indent=2)
        st.download_button(
            label="📄 Tải xuống kết quả (JSON)",
            data=json_results,
            file_name="analysis_results.json",
            mime="application/json"
        )
        
        # Export as CSV
        export_data = []
        for cluster, summary in results.items():
            export_data.append({
                'Cluster': cluster,
                'Summary': summary,
                'Record_Count': len(df[df['Cluster'] == cluster])
            })
        export_df = pd.DataFrame(export_data)
        
        csv_data = export_df.to_csv(index=False)
        st.download_button(
            label="📊 Tải xuống kết quả (CSV)",
            data=csv_data,
            file_name="analysis_results.csv",
            mime="text/csv"
        )

except Exception as e:
    st.error(f"❌ Lỗi khi xử lý file: {str(e)}")
    st.info("💡 Vui lòng kiểm tra định dạng file Excel và tham số cấu hình.")
