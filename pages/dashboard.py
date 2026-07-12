# pages/dashboard.py
import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.graph_objects as go
import textwrap
# PERBAIKAN: Hanya import fungsi yang benar-benar digunakan dan mendukung time_filter
from database.db import get_mood_stats_all, get_daily_trends

# Konfigurasi halaman & Sidebar Filter
st.sidebar.header("Dashboard Filter")
time_filter = st.sidebar.selectbox(
    "Select View Range",
    options=["Hari Ini (Today)", "Minggu Ini (Weekly View)", "Semua Data (All Time)"],
    index=1  # Default langsung ke Weekly View
)

# Judul Halaman
st.markdown("<h1 style='margin-bottom: 0px; font-weight: 800; font-size: 30px; color: #1E293B;'>Student Mood Overview</h1>", unsafe_allow_html=True)
st.markdown("<p style='margin-top: 5px; color: #64748B; font-size: 15px; margin-bottom: 30px;'>Real-time emotional monitoring and student well-being analytics.</p>", unsafe_allow_html=True)

# Ambil data dari database berdasarkan filter waktu
df_all = get_mood_stats_all(time_filter)
df_trends = get_daily_trends(time_filter)

# Helper CSS untuk metric cards
st.markdown("""
<style>
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));x`
        gap: 20px;
        margin-bottom: 30px;
    }
    .m-card {
        background: white;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .m-title {
        font-size: 11px;
        font-weight: 700;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 8px;
    }
    .m-value {
        font-size: 32px;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
        margin-bottom: 10px;
    }
    .m-badge {
        font-size: 11px;
        font-weight: 600;
        padding: 4px 8px;
        border-radius: 6px;
        align-self: flex-start;
    }
    .badge-blue { background-color: #EFF6FF; color: #3B82F6; }
    .badge-green { background-color: #ECFDF5; color: #10B981; }
    .badge-orange { background-color: #FFFBEB; color: #F59E0B; }
    .badge-red { background-color: #FEF2F2; color: #EF4444; }
</style>
""", unsafe_allow_html=True)

if not df_all.empty:
    # Kalkulasi metrik secara dinamis berdasarkan data hasil filter
    total_scans = len(df_all)
    total_students = df_all['student_id'].nunique() if 'student_id' in df_all.columns else 0
    
    happy_count = len(df_all[df_all['emotion'] == 'Happy'])
    neutral_count = len(df_all[df_all['emotion'] == 'Neutral'])
    sad_count = len(df_all[df_all['emotion'].isin(['Sad', 'Angry'])])
    
    happy_pct = int((happy_count / total_scans * 100)) if total_scans > 0 else 0
    neutral_pct = int((neutral_count / total_scans * 100)) if total_scans > 0 else 0
    sad_pct = int((sad_count / total_scans * 100)) if total_scans > 0 else 0
    
    # Render Metric Cards
    st.markdown(f"""
<div class="metric-grid">
    <div class="m-card">
        <span class="m-title">Total Students</span>
        <span class="m-value">{total_students}</span>
        <span class="m-badge badge-orange">Active Registry</span>
    </div>
    <div class="m-card">
        <span class="m-title">Scans Recorded</span>
        <span class="m-value">{total_scans}</span>
        <span class="m-badge badge-blue">{time_filter}</span>
    </div>
    <div class="m-card">
        <span class="m-title">Happy Students</span>
        <span class="m-value">{happy_count}</span>
        <span class="m-badge badge-green">{happy_pct}% of scans</span>
    </div>
    <div class="m-card">
        <span class="m-title">Neutral Students</span>
        <span class="m-value">{neutral_count}</span>
        <span class="m-badge badge-blue">{neutral_pct}% of scans</span>
    </div>
    <div class="m-card">
        <span class="m-title">Attention Needed</span>
        <span class="m-value">{sad_count}</span>
        <span class="m-badge badge-red">{sad_pct}% (Sad/Angry)</span>
    </div>
</div>
""", unsafe_allow_html=True)

    # Kolom Tengah (Charts)
    col_trend, col_dist = st.columns([3, 2])
    
    with col_trend:
        st.markdown("<div style='background-color: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);'>", unsafe_allow_html=True)
        
        chart_title = "Hourly Emotion Trend" if time_filter == "Hari Ini (Today)" else "Daily Emotion Trend"
        st.markdown(f"<h3 style='margin: 0px 0px 15px 0px; font-size: 16px; font-weight: 700; color: #1E293B;'>{chart_title}</h3>", unsafe_allow_html=True)
        
        fig_trend = go.Figure()
        colors = {'Happy': '#10B981', 'Neutral': '#3B82F6', 'Sad': '#EF4444', 'Angry': '#F59E0B', 'Surprise': '#8B5CF6'}
        
        day_order = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        
        if not df_trends.empty and 'day_name' in df_trends.columns:
            trend_pivot = df_trends.pivot(index='day_name', columns='emotion', values='count').fillna(0)
            trend_pivot = trend_pivot.reindex(day_order).fillna(0)
            
            for emotion in trend_pivot.columns:
                if emotion in colors:
                    fig_trend.add_trace(go.Bar(
                        name=emotion,
                        x=day_order,
                        y=trend_pivot[emotion],
                        marker_color=colors[emotion],
                        marker_line_width=0,
                    ))
        else:
            fig_trend.update_layout(
                annotations=[dict(text="No trend data available for this range", showarrow=False, font=dict(color='#64748B'))]
            )
        
        fig_trend.update_layout(
            barmode='group',
            margin=dict(t=10, b=10, l=10, r=10),
            height=240,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1, font=dict(size=10, color='#64748B')),
            xaxis=dict(showgrid=False, tickfont=dict(color='#64748B', size=11)),
            yaxis=dict(showgrid=True, gridcolor='#F1F5F9', tickfont=dict(color='#64748B', size=11))
        )
        st.plotly_chart(fig_trend, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    with col_dist:
        st.markdown("<div style='background-color: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);'>", unsafe_allow_html=True)
        st.markdown("<h3 style='margin: 0px 0px 15px 0px; font-size: 16px; font-weight: 700; color: #1E293B;'>Emotion Distribution</h3>", unsafe_allow_html=True)
        
        count_col = 'id' if 'id' in df_all.columns else df_all.columns[0]
        counts = df_all.groupby('emotion')[count_col].count().reset_index().rename(columns={count_col: 'count'})
        
        color_sequence = [colors.get(x, '#64748B') for x in counts['emotion']]
        
        fig_dist = go.Figure(data=[go.Pie(
            labels=counts['emotion'], 
            values=counts['count'], 
            hole=.65,
            marker=dict(colors=color_sequence, line=dict(color='#FFFFFF', width=2)),
            textinfo='percent',
            hoverinfo='label+value',
            textposition='inside',
            showlegend=True
        )])
        
        fig_dist.update_layout(
            margin=dict(t=10, b=10, l=10, r=10),
            height=240,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation="v", font=dict(size=10, color='#64748B')),
            annotations=[dict(
                text=f"<span style='font-size:22px;font-weight:800;color:#0F172A;'>{total_scans}</span><br><span style='font-size:11px;color:#64748B;font-weight:600;'>Total Scans</span>",
                x=0.5, y=0.5, showarrow=False, align="center"
            )]
        )
        st.plotly_chart(fig_dist, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
        
    st.markdown("<br>", unsafe_allow_html=True)
    
    col_infra, col_support = st.columns([3, 2])
    
    with col_infra:
        st.markdown(textwrap.dedent("""
<div style="background-color: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); min-height: 250px; display: flex; flex-direction: column; justify-content: space-between;">
    <div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
            <h3 style="margin: 0; font-size: 16px; font-weight: 700; color: #1E293B; letter-spacing: -0.01em;">Technical Infrastructure</h3>
            <span style="font-size: 12px; color: #1E3A8A; font-weight: 600; background-color: #EFF6FF; padding: 4px 8px; border-radius: 6px;">v1.2 Stable</span>
        </div>
        <p style="font-size: 13px; color: #64748B; margin-bottom: 20px; line-height: 1.5;">Student Mood Monitoring System Architecture pipeline.</p>
        <div style="display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 8px; padding: 10px 0px;">
            <div style="text-align: center; border: 1px solid #BFDBFE; background-color: #EFF6FF; border-radius: 8px; padding: 8px; width: 85px; box-shadow: 0 2px 4px 0 rgba(0,0,0,0.02);">
                <div style="font-size: 18px;">📹</div>
                <div style="font-size: 10px; font-weight: 700; color: #1E3A8A; margin-top: 4px;">Webcam</div>
            </div>
            <div style="font-size: 14px; color: #94A3B8;">➔</div>
            <div style="text-align: center; border: 1px solid #BFDBFE; background-color: #EFF6FF; border-radius: 8px; padding: 8px; width: 85px; box-shadow: 0 2px 4px 0 rgba(0,0,0,0.02);">
                <div style="font-size: 18px;">🖼️</div>
                <div style="font-size: 10px; font-weight: 700; color: #1E3A8A; margin-top: 4px;">OpenCV</div>
            </div>
            <div style="font-size: 14px; color: #94A3B8;">➔</div>
            <div style="text-align: center; border: 1px solid #C7D2FE; background-color: #EEF2FF; border-radius: 8px; padding: 8px; width: 90px; box-shadow: 0 2px 4px 0 rgba(0,0,0,0.02);">
                <div style="font-size: 18px;">🧠</div>
                <div style="font-size: 10px; font-weight: 700; color: #4338CA; margin-top: 4px;">DCNN FER</div>
            </div>
            <div style="font-size: 14px; color: #94A3B8;">➔</div>
            <div style="text-align: center; border: 1px solid #A7F3D0; background-color: #ECFDF5; border-radius: 8px; padding: 8px; width: 85px; box-shadow: 0 2px 4px 0 rgba(0,0,0,0.02);">
                <div style="font-size: 18px;">🗄️</div>
                <div style="font-size: 10px; font-weight: 700; color: #047857; margin-top: 4px;">SQLite</div>
            </div>
            <div style="font-size: 14px; color: #94A3B8;">➔</div>
            <div style="text-align: center; border: 1px solid #A7F3D0; background-color: #ECFDF5; border-radius: 8px; padding: 8px; width: 85px; box-shadow: 0 2px 4px 0 rgba(0,0,0,0.02);">
                <div style="font-size: 18px;">📱</div>
                <div style="font-size: 10px; font-weight: 700; color: #047857; margin-top: 4px;">WhatsApp</div>
            </div>
        </div>
    </div>
</div>
"""), unsafe_allow_html=True)
        
    with col_support:
        st.markdown(textwrap.dedent("""
<div style="background-color: #ECFDF5; border: 1px solid #A7F3D0; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); min-height: 250px; display: flex; flex-direction: column; justify-content: space-between;">
    <div>
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 12px;">
            <span style="font-size: 20px;">💬</span>
            <h3 style="margin: 0; font-size: 16px; font-weight: 700; color: #065F46;">Automated Support</h3>
        </div>
        <p style="font-size: 12px; color: #047857; margin-bottom: 15px; line-height: 1.5;">When negative emotions (Sad, Angry) are detected repeatedly, the system sends supportive messages via WhatsApp Bot.</p>
        <div style="background-color: white; border-radius: 8px; padding: 12px; border: 1px solid #D1FAE5; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.02);">
            <div style="display: flex; justify-content: space-between; font-size: 10px; color: #059669; font-weight: 600; margin-bottom: 4px;">
                <span>MoodMonitor Bot</span>
                <span>10:48 AM</span>
            </div>
            <p style="font-size: 11.5px; color: #1F2937; margin: 0; font-style: italic; line-height: 1.4;">"Hello, we noticed you may not be feeling your best today. Remember that campus counseling is always here for you at room 204. Your mental health matters!"</p>
        </div>
    </div>
</div>
"""), unsafe_allow_html=True)
        if st.button("Configure Bot Triggers", use_container_width=True):
            st.success("Notification trigger configurations opened!")
            
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("<h3 style='margin: 0px 0px 15px 0px; font-size: 18px; font-weight: 800; color: #1E293B;'>Recent Detection Logs</h3>", unsafe_allow_html=True)
    
    df_recent = df_all.head(5)
    
    rows_html = ""
    for idx, row in df_recent.iterrows():
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
            
        conf = f"{row['confidence']:.1f}%"
        
        try:
            dt = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
            time_str = dt.strftime('%I:%M %p')
        except:
            time_str = row['timestamp']
            
        rows_html += f"""<tr style="border-bottom: 1px solid #F1F5F9;"><td style="padding: 12px 16px; font-weight: 600; color: #1E293B;">{row['student_name']}</td><td style="padding: 12px 16px;"><span style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 9999px; font-size: 11px; font-weight: 700; color: {color}; background-color: {bg_color}; text-transform: uppercase;"><span style="width: 5px; height: 5px; border-radius: 50%; background-color: {color};"></span>{emo}</span></td><td style="padding: 12px 16px; font-family: monospace; color: #334155; font-weight: 700; font-size: 13px;">{conf}</td><td style="padding: 12px 16px; color: #64748B; font-size: 12px;">{time_str}</td><td style="padding: 12px 16px;"><a href="#" style="color: #3B82F6; font-weight: 700; text-decoration: none; font-size: 12px;">View History</a></td></tr>"""
        
    table_html = f"""
<div style="overflow-x: auto; background-color: white; border: 1px solid #E2E8F0; border-radius: 12px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); margin-bottom: 15px;">
    <table style="width: 100%; border-collapse: collapse; text-align: left; font-family: sans-serif; font-size: 13px;">
        <thead>
            <tr style="background-color: #F8FAFC; border-bottom: 1px solid #E2E8F0; color: #475569; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em;">
                <th style="padding: 12px 16px;">STUDENT NAME</th>
                <th style="padding: 12px 16px;">EMOTION</th>
                <th style="padding: 12px 16px;">CONFIDENCE SCORE</th>
                <th style="padding: 12px 16px;">DETECTION TIME</th>
                <th style="padding: 12px 16px;">ACTIONS</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>
</div>
"""
    st.markdown(table_html, unsafe_allow_html=True)
    
    if st.button("View All Records", use_container_width=True):
        st.switch_page("pages/history.py")
else:
    st.warning("Belum ada data emosi yang tersimpan untuk rentang waktu ini.")