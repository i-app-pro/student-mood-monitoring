import cv2
import numpy as np
from keras.models import model_from_json
from collections import Counter

# ==========================================================
# GLOBAL VARIABLES
# ==========================================================

tracked_face = None
tracked_timer = 0

last_locked_emotion = "Neutral"

emotion_candidate = None
emotion_candidate_count = 0

# ==========================================================
# CONFIGURATION
# ==========================================================

BOX_COLOR = (45, 185, 255)
TEXT_COLOR = (255, 255, 255)


CENTER_COLOR = (0, 255, 255)
LINE_COLOR = (0, 255, 255)

CENTER_WEIGHT = 0.65
SIZE_WEIGHT = 0.35
TRACK_WEIGHT = 0.55

HIGH_THRESHOLD = 90
MEDIUM_THRESHOLD = 75

TRACK_MEMORY = 15

# ==========================================================
# LOAD MODEL
# ==========================================================

try:

    with open("models/emotiondetector.json", "r") as json_file:

        model = model_from_json(json_file.read())

    model.load_weights("models/emotiondetector.h5")

    print("Emotion model loaded.")

except Exception as e:

    print(e)

    model = None

# ==========================================================
# LABELS
# ==========================================================

emotion_labels = [
    "Angry",
    "Disgust",
    "Fear",
    "Happy",
    "Neutral",
    "Sad",
    "Surprise"
]

# ==========================================================
# FACE DETECTOR
# ==========================================================

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)

# ==========================================================
# HELPER
# ==========================================================

def calculate_distance(x1, y1, x2, y2):

    return np.sqrt(
        (x1-x2)**2 +
        (y1-y2)**2
    )


def calculate_blur(gray_face):

    return cv2.Laplacian(
        gray_face,
        cv2.CV_64F
    ).var()


def calculate_brightness(gray_face):

    return np.mean(gray_face)


def get_quality_status(blur, brightness):

    if blur < 70:

        return False

    if brightness < 40:

        return False

    return True

# ==========================================================
# MAIN PROCESS
# ==========================================================

def process_frame(frame, history=None):

    global tracked_face
    global tracked_timer

    global last_locked_emotion

    global emotion_candidate
    global emotion_candidate_count

    # ==========================================================
    # MODEL CHECK
    # ==========================================================

    if model is None:

        return frame, "Unknown", 0.0, {
            lbl: 0.0 for lbl in emotion_labels
        }

    # ==========================================================
    # PREPROCESS
    # ==========================================================

    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8,8)
    )

    gray = clahe.apply(gray)

    # ==========================================================
    # FACE DETECTION
    # ==========================================================

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.08,
        minNeighbors=7,
        minSize=(70,70),
        flags=cv2.CASCADE_SCALE_IMAGE
    )

    emotion = "Neutral"
    confidence = 0.0

    probabilities = {
        lbl:0.0
        for lbl in emotion_labels
    }

    frame_h, frame_w = frame.shape[:2]

    center_x = frame_w // 2
    center_y = frame_h // 2

    max_distance = np.sqrt(
        center_x**2 +
        center_y**2
    )

    best_face = None
    best_score = -999

    # ==========================================================
    # SELECT MAIN FACE
    # ==========================================================

    for (x,y,w,h) in faces:

        roi = gray[y:y+h, x:x+w]

        if roi.size == 0:
            continue

        blur = calculate_blur(roi)

        brightness = calculate_brightness(roi)

        quality_ok = get_quality_status(
            blur,
            brightness
        )

        if not quality_ok:
            continue

        face_center_x = x + w//2
        face_center_y = y + h//2

        distance = calculate_distance(
            face_center_x,
            face_center_y,
            center_x,
            center_y
        )

        center_score = 1 - (
            distance /
            max_distance
        )

        size_score = (
            w*h
        ) / (
            frame_w*frame_h
        )

        tracking_score = 0

        if tracked_face is not None:

            tx,ty,tw,th = tracked_face

            tracked_center_x = tx + tw//2
            tracked_center_y = ty + th//2

            track_distance = calculate_distance(
                face_center_x,
                face_center_y,
                tracked_center_x,
                tracked_center_y
            )

            max_track = np.sqrt(
                frame_w**2 +
                frame_h**2
            )

            tracking_score = 1 - (
                track_distance /
                max_track
            )

        score = (
            center_score * CENTER_WEIGHT +
            size_score * SIZE_WEIGHT +
            tracking_score * TRACK_WEIGHT
        )

        if score > best_score:

            best_score = score
            best_face = (
                x,
                y,
                w,
                h
            )

    # ==========================================================
    # NO FACE
    # ==========================================================

    if best_face is None:

        if tracked_timer < TRACK_MEMORY:

            tracked_timer += 1

        else:

            tracked_face = None

        return (
            frame,
            "No Face",
            0.0,
            probabilities
        )

    tracked_timer = 0

    tracked_face = best_face

    x,y,w,h = best_face
    
    # ==========================================================
    # EMOTION PREDICTION
    # ==========================================================

    roi_gray = gray[y:y+h, x:x+w]

    roi_gray = cv2.resize(
        roi_gray,
        (48,48)
    ).astype("float32") / 255.0

    roi_gray = np.expand_dims(
        np.expand_dims(
            roi_gray,
            axis=-1
        ),
        axis=0
    )

    prediction = model.predict(
        roi_gray,
        verbose=0
    )[0]

    probabilities = {
        emotion_labels[i]: float(prediction[i] * 100)
        for i in range(len(emotion_labels))
    }

    raw_idx = np.argmax(prediction)

    raw_emotion = emotion_labels[raw_idx]

    raw_confidence = float(prediction[raw_idx] * 100)
    
    
    # ============================
    # EMOTION SMOOTHING
    # ============================

    if history is not None:

        # Jika confidence sangat tinggi,
        # langsung gunakan prediksi terbaru
        if raw_confidence >= HIGH_THRESHOLD:

            history.clear()
            history.append(raw_emotion)

            emotion = raw_emotion
            confidence = raw_confidence

            # lock supaya tidak berubah karena noise
            last_locked_emotion = emotion

        else:

            history.append(raw_emotion)

            # voting mayoritas
            voted = Counter(history).most_common(1)[0][0]

            # jika hasil baru berbeda tetapi confidence kecil
            # gunakan emosi sebelumnya
            if (
                last_locked_emotion is not None
                and voted != last_locked_emotion
                and raw_confidence < MEDIUM_THRESHOLD
            ):

                emotion = last_locked_emotion

            else:

                emotion = voted
                last_locked_emotion = emotion

            selected_idx = emotion_labels.index(emotion)
            confidence = float(prediction[selected_idx] * 100)

    else:

        emotion = raw_emotion
        confidence = raw_confidence

    # ============================
    # DRAW RESULT
    # ============================

    face_center_x = x + w // 2
    face_center_y = y + h // 2

    # Bounding Box
    cv2.rectangle(
        frame,
        (x, y),
        (x + w, y + h),
        BOX_COLOR,
        3
    )

    # Garis ke titik tengah layar
    cv2.line(
        frame,
        (center_x, center_y),
        (face_center_x, face_center_y),
        LINE_COLOR,
        2
    )

    # Label Target
    cv2.putText(
        frame,
        "AI TARGET",
        (x, y - 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 255, 0),
        2
    )

    # Emotion
    cv2.putText(
        frame,
        f"{emotion} ({confidence:.1f}%)",
        (x, y - 8),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (0, 255, 0),
        2
    )

    # Confidence Status
    if confidence >= 90:
        status = "VERY HIGH"
        status_color = (0,255,0)

    elif confidence >= 80:
        status = "HIGH"
        status_color = (0,220,255)

    elif confidence >= 65:
        status = "MEDIUM"
        status_color = (0,180,255)

    else:
        status = "LOW"
        status_color = (0,0,255)

    cv2.putText(
        frame,
        f"Confidence : {status}",
        (x, y + h + 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        status_color,
        2
    )

    # Score wajah
    cv2.putText(
        frame,
        f"Target Score : {best_score:.2f}",
        (x, y + h + 48),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.55,
        TEXT_COLOR,
        2
    )

    # Jumlah wajah
    cv2.putText(
        frame,
        f"Detected Faces : {len(faces)}",
        (20,30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        TEXT_COLOR,
        2
    )

    # Titik tengah kamera
    cv2.circle(
        frame,
        (center_x, center_y),
        8,
        CENTER_COLOR,
        -1
    )

    cv2.putText(
        frame,
        "CENTER",
        (center_x + 12, center_y),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (0,255,255),
        2
    )

    return frame, emotion, confidence, probabilities