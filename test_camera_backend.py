import cv2
import time

backends = [
    ("DEFAULT", None),
    ("CAP_DSHOW", cv2.CAP_DSHOW),
    ("CAP_MSMF", cv2.CAP_MSMF)
]

for name, backend in backends:

    print("=" * 40)
    print(name)

    start = time.time()

    if backend is None:
        cap = cv2.VideoCapture(0)
    else:
        cap = cv2.VideoCapture(0, backend)

    elapsed = time.time() - start

    print("Open time:", elapsed)

    print("Opened:", cap.isOpened())

    cap.release()