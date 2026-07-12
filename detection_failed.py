# pages/detection.py
import streamlit as st 
import cv2
import numpy as np
from collections import deque
from services.realtime_emotion import process_frame
from services.save_mood import save_mood
# MENJADI SEPERTI INI:
from services.whatsapp_notification import trigger_whatsapp_notification
import time

# Header Halaman
st.markdown("<h1 style='margin-bottom: 0px; font-weight: 800; font-size: 30px; color: #1E293B;'>Real-time Emotion Detection</h1>", unsafe_allow_html=True)
st.markdown("<p style='margin-top: 5px; color: #64748B; font-size: 15px; margin-bottom: 30px;'>Neural analysis of student micro-expressions using FER Model.</p>", unsafe_allow_html=True)

# Daftar Mahasiswa untuk Log Database (Sudah ditambah nomor WhatsApp Orang Tua)
students_registry = [
    {"id": "#ST-2024-001", "name": "John Doe", "class": "CS-401A", "parent_phone": "6285725362878"},
    {"id": "#ST-2024-023", "name": "Sarah Miller", "class": "ENG-102B", "parent_phone": "6285725362878"},
    {"id": "#ST-2024-045", "name": "Alex Kim", "class": "MATH-201", "parent_phone": "6285725362878"},
    {"id": "#ST-2024-012", "name": "Emma Lawson", "class": "CS-401A", "parent_phone": "6285725362878"},
    {"id": "#ST-2024-009", "name": "Robert Chen", "class": "CS-401A", "parent_phone": "6285725362878"},
    {"id": "#ST-2024-015", "name": "Alice Thompson", "class": "ENG-102B", "parent_phone": "6285725362878"},
    {"id": "#ST-2024-032", "name": "Michael Watts", "class": "MATH-201", "parent_phone": "6285725362878"},
    {"id": "#ST-2024-055", "name": "Sophia Davis", "class": "PHYS-301", "parent_phone": "6285725362878"},
    {"id": "#ST-2024-077", "name": "David Wilson", "class": "PHYS-301", "parent_phone": "6285725362878"}
]

# Inisialisasi Session States
if "camera_active" not in st.session_state:
    st.session_state.camera_active = False

if "history_queue" not in st.session_state:
    st.session_state.history_queue = deque(maxlen=5)

if "last_emotion" not in st.session_state:
    st.session_state.last_emotion = "Neutral"

if "last_confidence" not in st.session_state:
    st.session_state.last_confidence = 0.0

if "last_probs" not in st.session_state:
    st.session_state.last_probs = {lbl: 0.0 for lbl in ["Angry", "Disgust", "Fear", "Happy", "Neutral", "Sad", "Surprise"]}

if "last_latency" not in st.session_state:
    st.session_state.last_latency = 0

if "cap" not in st.session_state:
    st.session_state.cap = None

# Session State Baru untuk Notifikasi WhatsApp Fonnte
if "sad_counter" not in st.session_state:
    st.session_state.sad_counter = 0

if "wa_sent_status" not in st.session_state:
    st.session_state.wa_sent_status = False

# Pembagian kolom halaman
col_left, col_right = st.columns([3, 2])

with col_left:
    # 1. Pendaftaran Siswa
    student_options = [f"{s['name']} ({s['id']} - {s['class']})" for s in students_registry]
    selected_student_idx = st.selectbox(
        "Pilih Mahasiswa untuk Logging", 
        range(len(student_options)), 
        format_func=lambda x: student_options[x]
    )
    selected_student = students_registry[selected_student_idx]
    
    # 2. Tombol Kontrol Kamera
    col_btn1, col_btn2, col_btn3 = st.columns(3)
    with col_btn1:
        if st.button("Start Camera", type="primary", use_container_width=True):
            st.session_state.camera_active = True
            st.session_state.sad_counter = 0     # Reset counter saat mulai baru
            st.session_state.wa_sent_status = False # Reset status WA saat mulai baru
            st.rerun()
    with col_btn2:
        if st.button("Stop Camera", use_container_width=True):
            st.session_state.camera_active = False
            if st.session_state.cap is not None:
                st.session_state.cap.release()
                st.session_state.cap = None
            st.rerun()
    with col_btn3:
        if st.button("Save Detection", use_container_width=True):
            save_mood(
                selected_student["id"],
                selected_student["name"],
                selected_student["class"],
                st.session_state.last_emotion,
                st.session_state.last_confidence
            )
            st.toast(f"✅ Data {selected_student['name']} berhasil disimpan.")

    # 3. Layar Camera Feed Placeholder
    camera_placeholder = st.empty()
    
    if not st.session_state.camera_active:
        camera_placeholder.markdown("""
<div style="background-color: #1E293B; border-radius: 12px; height: 360px; display: flex; align-items: center; justify-content: center; flex-direction: column; color: #94A3B8; border: 1px solid #334155; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
    <span style="font-size: 54px; margin-bottom: 12px;">🎥</span>
    <span style="font-size: 16px; font-weight: 700; color: #F1F5F9;">Kamera Offline</span>
    <span style="font-size: 12px; color: #64748B; margin-top: 4px;">Klik 'Start Camera' untuk mulai mendeteksi emosi siswa secara realtime.</span>
</div>
""", unsafe_allow_html=True)

    # 4. Pipeline Alur Analisis
    st.markdown("""
<div style="background-color: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); margin-top: 10px;">
    <h4 style="margin: 0 0 15px 0; font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Analysis Pipeline</h4>
    <div style="display: flex; align-items: center; justify-content: space-between; font-size: 11px; font-weight: 700; color: #475569; text-align: center;">
        <div style="flex: 1; padding: 8px; border: 1px solid #E2E8F0; background-color: #F8FAFC; border-radius: 6px;">📹 WEBCAM</div>
        <div style="padding: 0 5px; color: #94A3B8;">➔</div>
        <div style="flex: 1; padding: 8px; border: 1px solid #E2E8F0; background-color: #F8FAFC; border-radius: 6px;">🖼️ OPENCV</div>
        <div style="padding: 0 5px; color: #94A3B8;">➔</div>
        <div style="flex: 1; padding: 8px; border: 1px solid #C7D2FE; background-color: #EEF2FF; border-radius: 6px; color: #4338CA;">🧠 FER MODEL</div>
        <div style="padding: 0 5px; color: #94A3B8;">➔</div>
        <div style="flex: 1; padding: 8px; border: 1px solid #A7F3D0; background-color: #ECFDF5; border-radius: 6px; color: #047857;">📊 RESULT</div>
    </div>
</div>
""", unsafe_allow_html=True)

with col_right:
    right_placeholder = st.empty()

# Fungsi untuk render panel kanan
def render_right_column(emotion, confidence, probs, latency):
    colors = {
        'Happy': '#10B981', 'Neutral': '#3B82F6', 'Sad': '#EF4444', 
        'Angry': '#EF4444', 'Surprise': '#8B5CF6', 'Disgust': '#F59E0B', 
        'Fear': '#F59E0B', 'Unknown': '#64748B', 'No Face': '#64748B'
    }
    color = colors.get(emotion, '#64748B')
    
    prob_bars = ""
    for label in ["Happy", "Neutral", "Sad", "Angry", "Surprise"]:
        val = probs.get(label, 0.0)
        prob_bars += f"""<div style="margin-bottom: 12px;"><div style="display: flex; justify-content: space-between; font-size: 12px; font-weight: 600; color: #475569; margin-bottom: 4px;"><span>{label}</span><span>{val:.1f}%</span></div><div style="background-color: #F1F5F9; height: 8px; border-radius: 4px; overflow: hidden;"><div style="background-color: {colors.get(label, '#3B82F6')}; width: {val}%; height: 100%; border-radius: 4px;"></div></div></div>"""
        
    status_text = 'Active' if st.session_state.camera_active else 'Inactive'
    status_color = '#10B981' if st.session_state.camera_active else '#EF4444'
    
    html = f"""
<div style="background-color: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); margin-bottom: 20px;">
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #F1F5F9; padding-bottom: 15px; margin-bottom: 15px;">
        <div>
            <span style="font-size: 10px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Current Status</span>
            <div style="display: flex; align-items: center; gap: 6px; font-size: 15px; font-weight: 700; color: {status_color};">
                <span style="width: 8px; height: 8px; border-radius: 50%; background-color: {status_color};"></span>
                {status_text}
            </div>
        </div>
        <div style="text-align: right;">
            <span style="font-size: 10px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Confidence</span>
            <div style="font-size: 24px; font-weight: 800; color: {color};">{confidence:.1f}%</div>
        </div>
    </div>
    <div style="margin-bottom: 20px;">
        <span style="font-size: 10px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Detected Emotion</span>
        <h2 style="margin: 5px 0 0 0; font-size: 38px; font-weight: 800; color: {color}; letter-spacing: -0.02em;">{emotion}</h2>
    </div>
    <div style="border-top: 1px solid #F1F5F9; padding-top: 15px; display: flex; justify-content: space-between; font-size: 12px; color: #64748B; font-weight: 600;">
        <span>Processing Latency</span>
        <span style="color: #0F172A; font-family: monospace;">{latency}ms</span>
    </div>
</div>
<div style="background-color: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); margin-bottom: 20px;">
    <h4 style="margin: 0 0 15px 0; font-size: 13px; font-weight: 700; color: #1E293B; text-transform: uppercase; letter-spacing: 0.05em;">Classifiers</h4>
    {prob_bars}
</div>
<div style="background-color: #EFF6FF; border: 1px solid #BFDBFE; border-radius: 12px; padding: 15px; display: flex; gap: 12px; color: #1E3A8A;">
    <span style="font-size: 20px; line-height: 1;">ℹ️</span>
    <div>
        <div style="font-size: 12px; font-weight: 700; margin-bottom: 2px;">Model Version 2.4.1</div>
        <p style="font-size: 11px; margin: 0; line-height: 1.4; color: #1E40AF;">Deep Convolutional Neural Network (DCNN) trained on FER2013 dataset. Average validation accuracy: 88.4%.</p>
    </div>
</div>
"""
    return html

# Render awal panel kanan berdasarkan state terakhir
right_placeholder.markdown(
    render_right_column(
        st.session_state.last_emotion, 
        st.session_state.last_confidence, 
        st.session_state.last_probs, 
        st.session_state.last_latency
    ), 
    unsafe_allow_html=True
)

# Loop pemrosesan kamera internal real-time
if st.session_state.camera_active:
    if st.session_state.cap is None:
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        time.sleep(0.5)
        st.session_state.cap = cap

    cap = st.session_state.cap
    
    if not cap.isOpened():
        st.error("Gagal membuka kamera webcam. Pastikan kamera terhubung.")
        st.session_state.camera_active = False
    else:
        try:
            while st.session_state.camera_active:
                ret, frame = cap.read()
                if not ret:
                    continue

                process_start = time.time()
                
                # Kirim ke layanan pemrosesan FER
                frame_proc, emotion, confidence, probs = process_frame(
                    frame,
                    st.session_state.history_queue
                )

                process_time = int((time.time() - process_start) * 1000)
                latency = process_time

                # Update data internal agar sinkron
                st.session_state.last_emotion = emotion
                st.session_state.last_confidence = confidence
                st.session_state.last_probs = probs
                st.session_state.last_latency = latency

                # Logika Penghitung Emosi Negatif & Pemicu Notifikasi WhatsApp via Fonnte
                if emotion in ["Sad", "Angry", "Fear"]:
                    st.session_state.sad_counter += 1
                    
                    # Jika emosi negatif terdeteksi berurutan selama >= 50 frame dan belum terkirim WA
                    if st.session_state.sad_counter >= 50 and not st.session_state.wa_sent_status:
                        parent_phone = selected_student.get("parent_phone")
                        student_name = selected_student.get("name")
                        
                        if parent_phone:
                            # Menggunakan background threading agar kamera anti-freeze
                            trigger_whatsapp_notification(parent_phone, student_name, emotion)
                            st.session_state.wa_sent_status = True
                            st.toast(f"📱 WhatsApp Notifikasi dikirim ke orang tua {student_name}.")
                else:
                    # Jika emosi normal kembali, kurangi counternya pelan-pelan
                    if st.session_state.sad_counter > 0:
                        st.session_state.sad_counter -= 1

                # Render citra ke layar utama (Konversi BGR ke RGB)
                frame_rgb = cv2.cvtColor(frame_proc, cv2.COLOR_BGR2RGB)
                camera_placeholder.image(frame_rgb, use_container_width=True)

                # Pembaruan in-place panel kanan
                right_placeholder.markdown(
                    render_right_column(emotion, confidence, probs, latency),
                    unsafe_allow_html=True
                )
                
                # Jeda mikro agar sistem seimbang
                time.sleep(0.01)
                
        except Exception as e:
            st.error(f"Streaming Error : {e}")
            if st.session_state.cap is not None:
                st.session_state.cap.release()
                st.session_state.cap = None
            st.session_state.camera_active = False
            st.rerun()