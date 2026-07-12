import cv2
import numpy as np
from collections import Counter, deque

from keras.models import model_from_json

# ==========================
# LOAD MODEL
# ==========================
with open("models/emotiondetector.json", "r") as json_file:
    model_json = json_file.read()

model = model_from_json(model_json)
model.load_weights("models/emotiondetector.h5")

print("Model berhasil dimuat!")

# ==========================
# LABEL EMOSI
# ==========================
emotion_labels = [
    "Angry",
    "Disgust",
    "Fear",
    "Happy",
    "Neutral",
    "Sad",
    "Surprise"
]

# ==========================
# FACE DETECTOR
# ==========================
face_detector = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)

# ==========================
# CAMERA
# ==========================
cap = cv2.VideoCapture(0)

# Simpan 15 prediksi terakhir
emotion_history = deque(maxlen=15)

while True:

    ret, frame = cap.read()

    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_detector.detectMultiScale(
        gray,
        scaleFactor=1.3,
        minNeighbors=5
    )

    for (x, y, w, h) in faces:

        roi_gray = gray[y:y+h, x:x+w]

        roi_gray = cv2.resize(
            roi_gray,
            (48, 48)
        )

        roi_gray = roi_gray.astype("float32") / 255.0

        roi_gray = np.expand_dims(
            roi_gray,
            axis=-1
        )

        roi_gray = np.expand_dims(
            roi_gray,
            axis=0
        )

        prediction = model.predict(
            roi_gray,
            verbose=0
        )

        emotion_index = np.argmax(prediction)

        confidence = prediction[0][emotion_index] * 100

        emotion = emotion_labels[emotion_index]

        # ==========================
        # SMOOTHING
        # ==========================
        emotion_history.append(emotion)

        most_common = Counter(
            emotion_history
        ).most_common(1)[0][0]

        # ==========================
        # DRAW
        # ==========================
        cv2.rectangle(
            frame,
            (x, y),
            (x+w, y+h),
            (0, 255, 0),
            2
        )

        text = f"{most_common} ({confidence:.1f}%)"

        cv2.putText(
            frame,
            text,
            (x, y-10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (0, 255, 0),
            2
        )

    cv2.imshow(
        "Student Mood Monitoring",
        frame
    )

    if cv2.waitKey(1) & 0xFF == 27:
        break

cap.release()
cv2.destroyAllWindows()