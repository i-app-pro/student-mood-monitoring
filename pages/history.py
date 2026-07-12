# pages/history.py
import streamlit as st
import pandas as pd
from datetime import datetime
from database.db import get_mood_stats_all
import textwrap

# Header Halaman
st.markdown("<h1 style='margin-bottom: 0px; font-weight: 800; font-size: 30px; color: #1E293B;'>Student Records</h1>", unsafe_allow_html=True)
st.markdown("<p style='margin-top: 5px; color: #64748B; font-size: 15px; margin-bottom: 30px;'>Comprehensive database of historical emotion detection logs and academic well-being scores.</p>", unsafe_allow_html=True)

# AMBIL SEMUA DATA (ALL TIME): Memaksa query menarik seluruh data historis dari database
df = get_mood_stats_all("Semua Data (All Time)")

# Helper CSS untuk tampilan halaman records
st.markdown("""
<style>
    .rec-metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 20px;
        margin-bottom: 25px;
    }
    .r-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
    }
    .r-title {
        font-size: 10px;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .r-value {
        font-size: 26px;
        font-weight: 800;
        color: #0F172A;
    }
    .r-subtext {
        font-size: 11px;
        color: #94A3B8;
        margin-top: 4px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)

if not df.empty:
    # 1. Metrik Akumulatif Dinamis (Dihitung dari seluruh data database)
    total_records = len(df)
    avg_confidence = df['confidence'].mean()
    
    # Mood Alert Ratio (Sad & Angry)
    alert_count = len(df[df['emotion'].isin(['Sad', 'Angry'])])
    alert_ratio = (alert_count / total_records * 100) if total_records > 0 else 0
    
    # Classes Monitored
    unique_classes = df['class_name'].nunique()
    
    st.markdown(f"""
    <div class="rec-metric-grid">
        <div class="r-card">
            <div class="r-title">Total Records</div>
            <div class="r-value">{total_records:,}</div>
            <div class="r-subtext" style="color: #3B82F6;">All-time database logs</div>
        </div>
        <div class="r-card">
            <div class="r-title">Avg. Confidence</div>
            <div class="r-value">{avg_confidence:.1f}%</div>
            <div class="r-subtext" style="color: #10B981;">Optimal accuracy</div>
        </div>
        <div class="r-card">
            <div class="r-title">Mood Alert Ratio</div>
            <div class="r-value">{alert_ratio:.1f}%</div>
            <div class="r-subtext" style="color: #EF4444;">Attention required</div>
        </div>
        <div class="r-card">
            <div class="r-title">Classes Monitored</div>
            <div class="r-value">{unique_classes}</div>
            <div class="r-subtext" style="color: #F59E0B;">Across Departments</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # 2. Filter & Pencarian Multikolom
    st.markdown("<h4 style='font-size: 15px; font-weight: 700; color: #1E293B; margin-bottom: 10px;'>🔍 Search & Advanced Filters</h4>", unsafe_allow_html=True)
    
    col_name, col_class, col_date = st.columns([2, 1, 1])
    
    with col_name:
        search_name = st.text_input("Student Name", "", placeholder="e.g. John Doe")
    
    with col_class:
        search_class = st.text_input("Class Name", "", placeholder="e.g. CS-401A")
        
    with col_date:
        search_date = st.text_input("Date (YYYY-MM-DD)", "", placeholder="e.g. 2026-06-29")
    
    emotion_filter = st.radio(
        "Filter by Emotion Status:",
        ["All Records", "Happy", "Neutral", "Sad", "Surprise", "Angry"],
        horizontal=True
    )
        
    # Proses Filter Gabungan menggunakan Pandas DataFrame
    df_filtered = df.copy()
    
    if search_name:
        df_filtered = df_filtered[df_filtered['student_name'].str.contains(search_name, case=False, na=False)]
        
    if search_class:
        df_filtered = df_filtered[df_filtered['class_name'].str.contains(search_class, case=False, na=False)]
        
    if search_date:
        df_filtered = df_filtered[df_filtered['timestamp'].str.contains(search_date, na=False)]
        
    if emotion_filter != "All Records":
        df_filtered = df_filtered[df_filtered['emotion'] == emotion_filter]

    # 3. Tombol Ekspor CSV Dinamis (Mengikuti hasil pencarian di layar)
    col_count, col_export = st.columns([3, 1])
    with col_count:
        st.markdown(f"<p style='color: #64748B; font-size: 13px; font-weight: 500;'>Showing {len(df_filtered)} of {total_records} logs</p>", unsafe_allow_html=True)
    with col_export:
        csv_data = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Export Result (CSV)",
            data=csv_data,
            file_name=f"filtered_mood_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # 4. Tabel / Pagination Card System
    items_per_page = 8
    total_items = len(df_filtered)
    total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    
    if total_items > 0:
        page = st.number_input(
            f"Page (1 to {total_pages})", 
            min_value=1, 
            max_value=total_pages, 
            value=1, 
            step=1
        )
        
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, total_items)
        df_page = df_filtered.iloc[start_idx:end_idx]
        
        cards_html = ""
        for idx, row in df_page.iterrows():
            emo = row['emotion']
            color = "#64748B"
            bg_color = "#F1F5F9"
            if emo == "Happy":
                color = "#10B981"
                bg_color = "#D1FAE5"
            elif emo == "Neutral":
                color = "#3B82F6"
                bg_color = "#DBEAFE"
            elif emo in ["Sad", "Angry"]:
                color = "#EF4444"
                bg_color = "#FEE2E2"
            elif emo == "Surprise":
                color = "#8B5CF6"
                bg_color = "#F3E8FF"
                
            conf = row['confidence']
            
            try:
                dt = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
                time_str = dt.strftime('%d %b %Y, %I:%M %p')
            except:
                time_str = row['timestamp']
                
            initials = "".join([part[0] for part in row['student_name'].split()[:2]])
            
            cards_html += textwrap.dedent(f"""
            <div style="background-color: white; border: 1px solid #E2E8F0; border-left: 5px solid {color}; border-radius: 12px; padding: 16px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.02); font-family: sans-serif;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="width: 38px; height: 38px; border-radius: 50%; background-color: #F1F5F9; color: #475569; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; border: 1px solid #E2E8F0;">
                        {initials}
                    </div>
                    <div>
                        <div style="font-weight: 700; color: #1F2937; font-size: 15px;">{row['student_name']}</div>
                        <div style="font-size: 11.5px; color: #64748B; font-weight: 600; margin-top: 2px;">
                            ID: <span style="font-family: monospace; color: #475569;">{row['student_id']}</span> &nbsp;|&nbsp; Class: <span style="color: #475569;">{row['class_name']}</span>
                        </div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 20px;">
                    <div style="text-align: right;">
                        <span style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 9999px; font-size: 10px; font-weight: 700; color: {color}; background-color: {bg_color}; text-transform: uppercase; letter-spacing: 0.05em;">
                            <span style="width: 5px; height: 5px; border-radius: 50%; background-color: {color};"></span>
                            {emo}
                        </span>
                        <div style="font-size: 10.5px; color: #94A3B8; font-weight: 600; margin-top: 4px; font-family: monospace;">Confidence: {conf:.1f}%</div>
                    </div>
                    <div style="text-align: right; min-width: 130px;">
                        <div style="font-size: 12.5px; color: #475569; font-weight: 600;">{time_str}</div>
                        <div style="font-size: 10.5px; color: #94A3B8; font-weight: 500; margin-top: 4px;">Recorded Log</div>
                    </div>
                </div>
            </div>
            """)
            
        st.markdown(cards_html, unsafe_allow_html=True)
    else:
        st.info("Tidak ada catatan mood yang cocok dengan kriteria pencarian/filter.")
else:
    st.warning("Belum ada data emosi yang tersimpan di database.")