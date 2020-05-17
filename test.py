import cv2
import time
from datetime import datetime
import os

import sys

import numpy as np
import cv2

capture_height = 2464
capture_width = 3280
frame_rate = 10
display_width = 860
display_height = 640
flip_method = 0

gstr = ("nvarguscamerasrc sensor-id=0 ! video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, format=(string)NV12, framerate=(fraction)%d/1 ! nvvidconv flip-method=%d ! video/x-raw, width=(int)%d, height=(int)%d ! videoconvert ! video/x-raw, format=(string)BGR ! appsink"
        % (capture_width, capture_height, frame_rate, flip_method, 
        display_width, display_height))
print(gstr)
filename = 'video.avi'
fourcc = cv2.VideoWriter_fourcc(*'XVID')

cap = cv2.VideoCapture(gstr, cv2.CAP_GSTREAMER)
out = cv2.VideoWriter(filename, fourcc, float(frame_rate),
                      (display_width*2, display_height%2), True)

while True:
    ret, img = cap.read()
    out.write(img)
    cv2.imshow('img',img)
    if cv2.waitKey(1) & 0xff == ord('q'):
        break

cap.release()
out.release()
cv2.destroyAllWindows()

 
def read_cam():
    cap = cv2.VideoCapture("nvarguscamerasrc sensor-id=0 ! video/x-raw(memory:NVMM), width=(int)3280, height=(int)2464, format=(string)NV12, framerate=(fraction)10/1 ! nvvidconv flip-method=0 ! video/x-raw, width=(int)1640, height=(int)1232 ! videoconvert ! video/x-raw, format=(string)BGR ! appsink", cv2.CAP_GSTREAMER)
    if cap.isOpened():
        cv2.namedWindow("demo", cv2.WINDOW_AUTOSIZE)
        while True:
            ret_val, img = cap.read()
            cv2.imshow('demo',img)
            cv2.waitKey(10)
    else:
        print ("camera open failed")
 
    cv2.destroyAllWindows()

read_cam()

def gstreamer_pipeline(
    capture_width=1280,
    capture_height=720,
    display_width=1280,
    display_height=720,
    framerate=60,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=0 sensor-mode=4  wbmode=1 ! "
        "video/x-raw(memory:NVMM), "
        "width=(int)%d, height=(int)%d, "
        "format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
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
    sensor_id=0,
    capture_width=3280,
    capture_height=2464,
    display_width=3280,
    display_height=2464,
    framerate=60,
    flip_method=0,
):
    return (
        "nvarguscamerasrc sensor-id=%d ! "
        "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, format=(string)NV12, framerate=(fraction)%d/1 ! "
        "nvvidconv flip-method=%d ! "
        "video/x-raw, width=(int)%d, height=(int)%d ! "
        "videoconvert ! video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )
 
def save_image():    
    print(gstreamer_pipeline_2(flip_method=0, capture_height=2464, capture_width=3280, framerate=10))
    cap = cv2.VideoCapture(gstreamer_pipeline_2(
        sensor_id=0,
        flip_method=1, 
        capture_height=3280, 
        capture_width=2464, 
        framerate=10, 
        display_height=3280, 
        display_width=2464
        ), cv2.CAP_GSTREAMER)

    while(cap.isOpened()):
        ret_val, img = cap.read()
        if ret_val:
            cv2.imwrite("/tmp/ramdisk/test.jpg", img)
            break
    cap.release()
 
print(datetime.now())
save_image()
print(datetime.now())
cmd='nvgstcapture-1.0 -A --capture-auto -S 0 --image-res=3 --file-name=capture.jpg'
os.system(cmd)
print(datetime.now())
cmd='''gst-launch-1.0 nvarguscamerasrc num-buffers=1 ! 'video/x-raw(memory:NVMM), width=1920, height=1080, format=NV12' ! nvjpegenc ! filesink location=test.jpg'''
os.system(cmd)
print(datetime.now())