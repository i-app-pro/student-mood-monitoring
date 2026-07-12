# # # database/db.py
# # import sqlite3
# # import pandas as pd
# # import os
# # import random
# # from datetime import datetime, timedelta

# # def get_db_connection():
# #     # Pastikan folder database ada
# #     if not os.path.exists('database'):
# #         os.makedirs('database')
# #     conn = sqlite3.connect('database/database.db')
# #     return conn

# # def init_db():
# #     conn = get_db_connection()
# #     cursor = conn.cursor()
    
# #     # Membuat tabel terpadu student_mood_logs
# #     cursor.execute('''
# #         CREATE TABLE IF NOT EXISTS student_mood_logs (
# #             id INTEGER PRIMARY KEY AUTOINCREMENT,
# #             student_id TEXT NOT NULL,
# #             student_name TEXT NOT NULL,
# #             class_name TEXT NOT NULL,
# #             emotion TEXT NOT NULL,
# #             confidence REAL NOT NULL,
# #             timestamp DATETIME NOT NULL
# #         )
# #     ''')
# #     conn.commit()
    
# #     # Periksa apakah tabel kosong, jika ya buat mock data
# #     cursor.execute("SELECT COUNT(*) FROM student_mood_logs")
# #     count = cursor.fetchone()[0]
    
# #     if count == 0:
# #         # Mock students
# #         students = [
# #             ("#ST-2024-001", "John Doe", "CS-401A"),
# #             ("#ST-2024-023", "Sarah Miller", "ENG-102B"),
# #             ("#ST-2024-045", "Alex Kim", "MATH-201"),
# #             ("#ST-2024-012", "Emma Lawson", "CS-401A"),
# #             ("#ST-2024-009", "Robert Chen", "CS-401A"),
# #             ("#ST-2024-015", "Alice Thompson", "ENG-102B"),
# #             ("#ST-2024-032", "Michael Watts", "MATH-201"),
# #             ("#ST-2024-055", "Sophia Davis", "PHYS-301"),
# #             ("#ST-2024-077", "David Wilson", "PHYS-301"),
# #             ("#ST-2024-088", "Lily Evans", "CHEM-101"),
# #             ("#ST-2024-099", "James Potter", "CHEM-101"),
# #             ("#ST-2024-110", "Tom Riddle", "CS-401A")
# #         ]
        
# #         # Proporsi emosi
# #         emotions = ["Happy", "Neutral", "Sad", "Angry", "Surprise"]
# #         emotion_weights = [0.47, 0.33, 0.12, 0.05, 0.03]
        
# #         now = datetime.now()
        
# #         # Buat sekitar 180 catatan mood historis selama 7 hari terakhir
# #         for _ in range(180):
# #             student_id, name, class_name = random.choice(students)
# #             emotion = random.choices(emotions, weights=emotion_weights, k=1)[0]
            
# #             # Confidence score sesuai dengan emosi
# #             if emotion == "Happy":
# #                 confidence = round(random.uniform(85.0, 99.5), 1)
# #             elif emotion == "Neutral":
# #                 confidence = round(random.uniform(75.0, 95.0), 1)
# #             else:
# #                 confidence = round(random.uniform(65.0, 90.0), 1)
            
# #             # Timestamp acak dalam 7 hari terakhir pada jam sekolah (08:00 - 17:00)
# #             days_ago = random.randint(0, 6)
# #             hour = random.randint(8, 17)
# #             minute = random.randint(0, 59)
# #             second = random.randint(0, 59)
# #             log_time = now - timedelta(days=days_ago)
# #             log_time = log_time.replace(hour=hour, minute=minute, second=second)
            
# #             cursor.execute('''
# #                 INSERT INTO student_mood_logs (student_id, student_name, class_name, emotion, confidence, timestamp)
# #                 VALUES (?, ?, ?, ?, ?, ?)
# #             ''', (student_id, name, class_name, emotion, confidence, log_time.strftime('%Y-%m-%d %H:%M:%S')))
            
# #         conn.commit()
# #     conn.close()

# # def get_mood_stats_all():
# #     """Mengambil seluruh data logs untuk analisis mendalam di Streamlit"""
# #     conn = get_db_connection()
# #     query = "SELECT * FROM student_mood_logs ORDER BY timestamp DESC"
# #     df = pd.read_sql_query(query, conn)
# #     conn.close()
# #     return df

# # def get_dashboard_metrics():
# #     """Mengambil ringkasan statistik untuk metrik dashboard utama"""
# #     conn = get_db_connection()
# #     cursor = conn.cursor()
    
# #     # Total scan hari ini
# #     today_str = datetime.now().strftime('%Y-%m-%d')
# #     cursor.execute("SELECT COUNT(*) FROM student_mood_logs WHERE date(timestamp) = ?", (today_str,))
# #     scans_today = cursor.fetchone()[0]
    
# #     # Jika hari ini belum ada scan, ambil scan dari hari terakhir yang ada data
# #     if scans_today == 0:
# #         cursor.execute("SELECT date(timestamp) FROM student_mood_logs ORDER BY timestamp DESC LIMIT 1")
# #         res = cursor.fetchone()
# #         if res:
# #             today_str = res[0]
# #             cursor.execute("SELECT COUNT(*) FROM student_mood_logs WHERE date(timestamp) = ?", (today_str,))
# #             scans_today = cursor.fetchone()[0]
            
# #     # Hitung jumlah per emosi untuk hari terpilih (untuk metrics)
# #     cursor.execute("""
# #         SELECT emotion, COUNT(*) 
# #         FROM student_mood_logs 
# #         WHERE date(timestamp) = ? 
# #         GROUP BY emotion
# #     """, (today_str,))
# #     counts = dict(cursor.fetchall())
    
# #     # Total mahasiswa unik yang terdaftar (mockup 120)
# #     cursor.execute("SELECT COUNT(DISTINCT student_id) FROM student_mood_logs")
# #     unique_students_in_db = cursor.fetchone()[0]
# #     total_students = max(120, unique_students_in_db) # setidaknya 120
    
# #     conn.close()
    
# #     return {
# #         "scans_today": scans_today,
# #         "happy_count": counts.get("Happy", 0),
# #         "neutral_count": counts.get("Neutral", 0),
# #         "sad_count": counts.get("Sad", 0) + counts.get("Angry", 0), # gabungkan emosi negatif
# #         "total_students": total_students,
# #         "date_str": today_str
# #     }

# # def get_daily_trends():
# #     """Mengambil trend harian (senin-minggu) dalam 7 hari terakhir"""
# #     conn = get_db_connection()
# #     query = """
# #         SELECT strftime('%w', timestamp) as day_num, 
# #                emotion, 
# #                COUNT(*) as count 
# #         FROM student_mood_logs 
# #         GROUP BY day_num, emotion
# #     """
# #     df = pd.read_sql_query(query, conn)
# #     conn.close()
    
# #     # Map angka ke nama hari
# #     day_map = {'0': 'Sun', '1': 'Mon', '2': 'Tue', '3': 'Wed', '4': 'Thu', '5': 'Fri', '6': 'Sat'}
# #     df['day_name'] = df['day_num'].map(day_map)
# #     return df





# # history.py lama

# # pages/history.py
# import streamlit as st
# import pandas as pd
# from datetime import datetime
# from database.db import get_mood_stats_all
# import textwrap

# # Header Halaman
# st.markdown("<h1 style='margin-bottom: 0px; font-weight: 800; font-size: 30px; color: #1E293B;'>Student Records</h1>", unsafe_allow_html=True)
# st.markdown("<p style='margin-top: 5px; color: #64748B; font-size: 15px; margin-bottom: 30px;'>Comprehensive database of historical emotion detection logs and academic well-being scores.</p>", unsafe_allow_html=True)

# # Ambil seluruh data dari database
# df = get_mood_stats_all()

# # Helper CSS untuk tampilan halaman records
# st.markdown("""
# <style>
#     .rec-metric-grid {
#         display: grid;
#         grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
#         gap: 20px;
#         margin-bottom: 25px;
#     }
#     .r-card {
#         background: white;
#         border: 1px solid #E2E8F0;
#         border-radius: 12px;
#         padding: 18px;
#         box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
#     }
#     .r-title {
#         font-size: 10px;
#         font-weight: 700;
#         color: #64748B;
#         text-transform: uppercase;
#         letter-spacing: 0.05em;
#         margin-bottom: 6px;
#     }
#     .r-value {
#         font-size: 26px;
#         font-weight: 800;
#         color: #0F172A;
#     }
#     .r-subtext {
#         font-size: 11px;
#         color: #94A3B8;
#         margin-top: 4px;
#         font-weight: 500;
#     }
# </style>
# """, unsafe_allow_html=True)

# if not df.empty:
#     # 1. Metrik Akumulatif Dinamis
#     total_records = len(df)
#     avg_confidence = df['confidence'].mean()
    
#     # Mood Alert Ratio (Sad & Angry)
#     alert_count = len(df[df['emotion'].isin(['Sad', 'Angry'])])
#     alert_ratio = (alert_count / total_records * 100) if total_records > 0 else 0
    
#     # Classes Monitored
#     unique_classes = df['class_name'].nunique()
    
#     st.markdown(f"""
#     <div class="rec-metric-grid">
#         <div class="r-card">
#             <div class="r-title">Total Records</div>
#             <div class="r-value">{total_records:,}</div>
#             <div class="r-subtext" style="color: #3B82F6;">+12% vs last month</div>
#         </div>
#         <div class="r-card">
#             <div class="r-title">Avg. Confidence</div>
#             <div class="r-value">{avg_confidence:.1f}%</div>
#             <div class="r-subtext" style="color: #10B981;">Optimal accuracy</div>
#         </div>
#         <div class="r-card">
#             <div class="r-title">Mood Alert Ratio</div>
#             <div class="r-value">{alert_ratio:.1f}%</div>
#             <div class="r-subtext" style="color: #EF4444;">Attention required</div>
#         </div>
#         <div class="r-card">
#             <div class="r-title">Classes Monitored</div>
#             <div class="r-value">{unique_classes}</div>
#             <div class="r-subtext" style="color: #F59E0B;">Across Departments</div>
#         </div>
#     </div>
#     """, unsafe_allow_html=True)

#     # 2. Filter & Pencarian
#     col_search, col_filter = st.columns([1, 2])
    
#     with col_search:
#         search_query = st.text_input("🔍 Search Student Name", "")
    
#     with col_filter:
#         emotion_filter = st.radio(
#             "Filter by Emotion:",
#             ["All Records", "Happy", "Neutral", "Sad", "Surprise", "Angry"],
#             horizontal=True
#         )
        
#     # Aplikasikan filter pencarian dan emosi
#     df_filtered = df.copy()
#     if search_query:
#         df_filtered = df_filtered[df_filtered['student_name'].str.contains(search_query, case=False)]
        
#     if emotion_filter != "All Records":
#         df_filtered = df_filtered[df_filtered['emotion'] == emotion_filter]

#     # 3. Tombol Ekspor CSV
#     col_count, col_export = st.columns([3, 1])
#     with col_count:
#         st.markdown(f"<p style='color: #64748B; font-size: 13px; font-weight: 500;'>Showing {len(df_filtered)} of {total_records} logs</p>", unsafe_allow_html=True)
#     with col_export:
#         # Generate CSV untuk diunduh
#         csv_data = df_filtered.to_csv(index=False).encode('utf-8')
#         st.download_button(
#             label="📥 Export Report (CSV)",
#             data=csv_data,
#             file_name=f"student_mood_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
#             mime="text/csv",
#             use_container_width=True
#         )

#     # 4. Tabel Kustom dengan Visual Progress Bar dan Dot Status
#     items_per_page = 8
#     total_items = len(df_filtered)
#     total_pages = max(1, (total_items + items_per_page - 1) // items_per_page)
    
#     if total_items > 0:
#         page = st.number_input(
#             f"Page (1 to {total_pages})", 
#             min_value=1, 
#             max_value=total_pages, 
#             value=1, 
#             step=1
#         )
        
#         start_idx = (page - 1) * items_per_page
#         end_idx = min(start_idx + items_per_page, total_items)
#         df_page = df_filtered.iloc[start_idx:end_idx]
        
#         cards_html = ""
#         for idx, row in df_page.iterrows():
#             # Pengaturan warna untuk Dot Status & Progress Bar
#             emo = row['emotion']
#             color = "#64748B"
#             bg_color = "#F1F5F9"
#             if emo == "Happy":
#                 color = "#10B981"
#                 bg_color = "#D1FAE5"
#             elif emo == "Neutral":
#                 color = "#3B82F6"
#                 bg_color = "#DBEAFE"
#             elif emo in ["Sad", "Angry"]:
#                 color = "#EF4444"
#                 bg_color = "#FEE2E2"
#             elif emo == "Surprise":
#                 color = "#8B5CF6"
#                 bg_color = "#F3E8FF"
                
#             conf = row['confidence']
            
#             # Format waktu agar human-readable
#             try:
#                 dt = datetime.strptime(row['timestamp'], '%Y-%m-%d %H:%M:%S')
#                 time_str = dt.strftime('%d %b %Y, %I:%M %p')
#             except:
#                 time_str = row['timestamp']
                
#             # Dapatkan inisial nama untuk avatar
#             initials = "".join([part[0] for part in row['student_name'].split()[:2]])
            
#             cards_html += textwrap.dedent(f"""
#             <div style="background-color: white; border: 1px solid #E2E8F0; border-left: 5px solid {color}; border-radius: 12px; padding: 16px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 1px 2px 0 rgba(0,0,0,0.02); transition: transform 0.2s; font-family: sans-serif;">
#                 <div style="display: flex; align-items: center; gap: 12px;">
#                     <div style="width: 38px; height: 38px; border-radius: 50%; background-color: #F1F5F9; color: #475569; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; border: 1px solid #E2E8F0;">
#                         {initials}
#                     </div>
#                     <div>
#                         <div style="font-weight: 700; color: #1F2937; font-size: 15px;">{row['student_name']}</div>
#                         <div style="font-size: 11.5px; color: #64748B; font-weight: 600; margin-top: 2px;">
#                             ID: <span style="font-family: monospace; color: #475569;">{row['student_id']}</span> &nbsp;|&nbsp; Class: <span style="color: #475569;">{row['class_name']}</span>
#                         </div>
#                     </div>
#                 </div>
#                 <div style="display: flex; align-items: center; gap: 20px;">
#                     <div style="text-align: right;">
#                         <span style="display: inline-flex; align-items: center; gap: 6px; padding: 4px 10px; border-radius: 9999px; font-size: 10px; font-weight: 700; color: {color}; background-color: {bg_color}; text-transform: uppercase; letter-spacing: 0.05em;">
#                             <span style="width: 5px; height: 5px; border-radius: 50%; background-color: {color};"></span>
#                             {emo}
#                         </span>
#                         <div style="font-size: 10.5px; color: #94A3B8; font-weight: 600; margin-top: 4px; font-family: monospace;">Confidence: {conf:.1f}%</div>
#                     </div>
#                     <div style="text-align: right; min-width: 130px;">
#                         <div style="font-size: 12.5px; color: #475569; font-weight: 600;">{time_str}</div>
#                         <div style="font-size: 10.5px; color: #94A3B8; font-weight: 500; margin-top: 4px;">Recorded Log</div>
#                     </div>
#                 </div>
#             </div>
#             """)
            
#         st.markdown(cards_html, unsafe_allow_html=True)
#     else:
#         st.info("Tidak ada log catatan mood yang cocok dengan kriteria pencarian/filter.")
# else:
#     st.warning("Belum ada data emosi yang tersimpan di database.")