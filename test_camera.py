import cv2
import time

t0 = time.time()

cap = cv2.VideoCapture(0)

print("Open:", time.time() - t0)

while True:
    ret, frame = cap.read()

    if not ret:
        break

    cv2.imshow("Camera", frame)

    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()



# test jalankan file python -m streamlit run app.py