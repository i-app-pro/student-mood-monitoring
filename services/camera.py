# services/camera.py
import cv2

def get_camera_frame():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        # Konversi BGR ke RGB agar warna di streamlit tidak terbalik
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        cap.release()
        return frame_rgb
    cap.release()
    return None