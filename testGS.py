import cv2
import time
from datetime import datetime
#gst-launch-1.0 nvarguscamerasrc exposuretimerange="5000000 5000000" ! 'video/x-raw(memory:NVMM),width=3820, height=2464, framerate=21/1, format=NV12' ! nvvidconv flip-method=0 ! 'video/x-raw,width=960, height=616' ! nvvidconv ! nvegltransform ! nveglglessink -e

def gstreamer_pipeline(
    capture_width=3264,
    capture_height=2464,
    display_width=3264,
    display_height=2464,
    framerate=21,
    flip_method=0,
):
    return (
        "nvarguscamerasrc exposuretimerange='20000000 20000000' exposurecompensation=1 sensor-id=0 ! "
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
        "nvarguscamerasrc sensor-id=0 ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)RGBA ! appsink"
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

def gstreamer_pipeline_3(
    capture_width=3280,
    capture_height=2464,
    display_width=3280,
    display_height=2464,
    framerate=60,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=0 ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv ! "
        "video/x-raw, format=(string)I420 ! appsink"
        # "videoconvert ! video/x-raw, format=(string)BGR ! appsink"
        % (
            capture_width,
            capture_height,
            framerate,
        )
    )

def gstreamer_pipeline_4(
    capture_width=3280,
    capture_height=2464,
    display_width=3280,
    display_height=2464,
    framerate=60,
    flip_method=0,
):
    return (
        "videotestsrc ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)I420, framerate=(fraction)%d/1 ! "
        "appsink "
        # "video/x-raw, format=(string)I420 ! appsink"
        # "videoconvert ! video/x-raw, format=(string)BGR ! appsink"
        % (
            capture_width,
            capture_height,
            framerate,
        )
    )

def gstreamer_pipeline_5(
    capture_width=3280,
    capture_height=2464,
    display_width=3280,
    display_height=2464,
    framerate=60,
    flip_method=0,
):
    return (
        "udpsrc port=5000 ! application/x-rtp,encoding-name=JPEG,payload=26 ! rtpjpegdepay !"
        "jpegdec ! video/x-raw, format=(string)I420 ! appsink"
    )


def save_image():
    print(gstreamer_pipeline(flip_method=0, capture_height=2464, capture_width=3280, framerate=21))
    cap = cv2.VideoCapture(gstreamer_pipeline(flip_method=0, capture_height=2464, capture_width=3264, display_height=2464, display_width=3264, framerate=21), cv2.CAP_GSTREAMER)
    delay=10
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
