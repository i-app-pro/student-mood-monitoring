# pages/detection.py (REFACTORED — pakai streamlit-webrtc)
import streamlit as st
# import cv2
import av
import time
import threading
from collections import deque
from streamlit_webrtc import webrtc_streamer, WebRtcMode, RTCConfiguration

from services.realtime_emotion import process_frame
from services.save_mood import save_mood
from services.whatsapp_notification import trigger_whatsapp_notification

# ==========================================================
# HEADER
# ==========================================================
st.markdown("<h1 style='margin-bottom: 0px; font-weight: 800; font-size: 30px; color: #1E293B;'>Real-time Emotion Detection</h1>", unsafe_allow_html=True)
st.markdown("<p style='margin-top: 5px; color: #64748B; font-size: 15px; margin-bottom: 30px;'>Neural analysis of student micro-expressions using FER Model.</p>", unsafe_allow_html=True)

# ==========================================================
# DAFTAR MAHASISWA
# ==========================================================
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

DEFAULT_PROBS = {lbl: 0.0 for lbl in ["Angry", "Disgust", "Fear", "Happy", "Neutral", "Sad", "Surprise"]}

RTC_CONFIGURATION = RTCConfiguration(
    {"iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]}
)

# ==========================================================
# VIDEO PROCESSOR — jalan di thread WebRTC (browser -> server)
# ==========================================================
class EmotionVideoProcessor:
    def __init__(self):
        self.history_queue = deque(maxlen=5)
        self.lock = threading.Lock()
        self.selected_student = None
        self.last_notified_student_id = ""
        self.result = {
            "emotion": "Neutral",
            "confidence": 0.0,
            "probs": DEFAULT_PROBS.copy(),
            "latency": 0,
            "just_notified": None,  # nama siswa kalau baru saja notif WA terkirim
        }

    def recv(self, frame):
        img = frame.to_ndarray(format="bgr24")

        start = time.time()
        frame_proc, emotion, confidence, probs = process_frame(img, self.history_queue)
        latency = int((time.time() - start) * 1000)

        just_notified = None

        with self.lock:
            student = self.selected_student

            # ==================== ANTI-SPAM WA (per siswa) ====================
            if student and emotion in ["Sad", "Angry", "Fear"] and confidence > 50.0:
                student_id = student.get("id")
                if self.last_notified_student_id != student_id:
                    parent_phone = student.get("parent_phone")
                    student_name = student.get("name")
                    if parent_phone:
                        trigger_whatsapp_notification(parent_phone, student_name, emotion)
                        self.last_notified_student_id = student_id
                        just_notified = student_name
            # ====================================================================

            self.result = {
                "emotion": emotion,
                "confidence": confidence,
                "probs": probs,
                "latency": latency,
                "just_notified": just_notified,
            }

        return av.VideoFrame.from_ndarray(frame_proc, format="bgr24")


# ==========================================================
# RENDER PANEL KANAN (sama seperti sebelumnya)
# ==========================================================
def render_right_column(emotion, confidence, probs, latency, camera_active):
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

    status_text = 'Active' if camera_active else 'Inactive'
    status_color = '#10B981' if camera_active else '#EF4444'

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


# ==========================================================
# SESSION STATE
# ==========================================================
if "last_emotion" not in st.session_state:
    st.session_state.last_emotion = "Neutral"
if "last_confidence" not in st.session_state:
    st.session_state.last_confidence = 0.0
if "last_probs" not in st.session_state:
    st.session_state.last_probs = DEFAULT_PROBS.copy()
if "last_latency" not in st.session_state:
    st.session_state.last_latency = 0

# ==========================================================
# LAYOUT
# ==========================================================
col_left, col_right = st.columns([3, 2])

with col_left:
    student_options = [f"{s['name']} ({s['id']} - {s['class']})" for s in students_registry]
    selected_student_idx = st.selectbox(
        "Pilih Mahasiswa untuk Logging",
        range(len(student_options)),
        format_func=lambda x: student_options[x],
    )
    selected_student = students_registry[selected_student_idx]

    # Widget kamera browser-based
    ctx = webrtc_streamer(
        key="emotion-detection",
        mode=WebRtcMode.SENDRECV,
        rtc_configuration=RTC_CONFIGURATION,
        video_processor_factory=EmotionVideoProcessor,
        media_stream_constraints={"video": True, "audio": False},
        async_processing=True,
    )

    # Kirim siswa yang dipilih ke processor (thread-safe)
    if ctx.video_processor:
        with ctx.video_processor.lock:
            ctx.video_processor.selected_student = selected_student

    if st.button("Save Detection", use_container_width=True):
        save_mood(
            selected_student["id"],
            selected_student["name"],
            selected_student["class"],
            st.session_state.last_emotion,
            st.session_state.last_confidence
        )
        st.toast(f"✅ Data {selected_student['name']} berhasil disimpan.")

    st.markdown("""
<div style="background-color: white; border: 1px solid #E2E8F0; border-radius: 12px; padding: 20px; box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05); margin-top: 10px;">
    <h4 style="margin: 0 0 15px 0; font-size: 11px; font-weight: 700; color: #64748B; text-transform: uppercase; letter-spacing: 0.05em;">Analysis Pipeline</h4>
    <div style="display: flex; align-items: center; justify-content: space-between; font-size: 11px; font-weight: 700; color: #475569; text-align: center;">
        <div style="flex: 1; padding: 8px; border: 1px solid #E2E8F0; background-color: #F8FAFC; border-radius: 6px;">📹 WEBCAM (Browser)</div>
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
    right_placeholder.markdown(
        render_right_column(
            st.session_state.last_emotion,
            st.session_state.last_confidence,
            st.session_state.last_probs,
            st.session_state.last_latency,
            camera_active=False,
        ),
        unsafe_allow_html=True,
    )

# ==========================================================
# LOOP UPDATE PANEL KANAN — baca hasil dari video processor thread
# ==========================================================
if ctx.state.playing:
    while ctx.state.playing:
        if ctx.video_processor:
            with ctx.video_processor.lock:
                result = dict(ctx.video_processor.result)

            st.session_state.last_emotion = result["emotion"]
            st.session_state.last_confidence = result["confidence"]
            st.session_state.last_probs = result["probs"]
            st.session_state.last_latency = result["latency"]

            right_placeholder.markdown(
                render_right_column(
                    result["emotion"],
                    result["confidence"],
                    result["probs"],
                    result["latency"],
                    camera_active=True,
                ),
                unsafe_allow_html=True,
            )

            if result["just_notified"]:
                st.toast(f"📱 WhatsApp Notifikasi dikirim ke orang tua {result['just_notified']}.")

        time.sleep(0.2)