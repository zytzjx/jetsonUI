import cv2
import time
from datetime import datetime

def gstreamer_pipeline(
    capture_width=3264,
    capture_height=2464,
    display_width=3264,
    display_height=2464,
    framerate=21,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=0 ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)RGBA !"
        "videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink"
        % (
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

def gstreamer_pipeline_2(
    capture_width=3280,
    capture_height=2464,
    display_width=3280,
    display_height=2464,
    framerate=60,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=1 ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)I420 ! appsink"
        # "videoconvert ! video/x-raw, format=(string)BGR ! appsink"
        % (
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

def save_image():
    print(gstreamer_pipeline(flip_method=0, capture_height=2464, capture_width=3280, framerate=21))
    cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0, capture_height=2464, capture_width=3264, display_height=2464, display_width=3264, framerate=21), cv2.CAP_GSTREAMER)
    delay=100
    while(cap.isOpened()):
        ret_val, img = cap.read()
        print("recv: " + datetime.now().strftime('%Y%m%d%H%M%S.%f'))
        delay-=1
        if(delay<0):
            # img1 = cv2.cvtColor(img, cv2.COLOR_YUV2BGR_NV12)
            # img2 = cv2.cvtColor(img, cv2.COLOR_YUV2BGR_I420)
            cv2.imwrite("test.jpg", img)
            break
    cap.release()

save_image()
