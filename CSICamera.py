# MIT License
# Copyright (c) 2019,2020 JetsonHacks
# See license
# A very simple code snippet
# Using two  CSI cameras (such as the Raspberry Pi Version 2) connected to a
# NVIDIA Jetson Nano Developer Kit (Rev B01) using OpenCV
# Drivers for the camera and OpenCV are included in the base image in JetPack 4.3+

# This script will open a window and place the camera stream from each camera in a window
# arranged horizontally.
# The camera streams are each read in their own thread, as when done sequentially there
# is a noticeable lag
# For better performance, the next step would be to experiment with having the window display
# in a separate thread

import cv2
import threading
import numpy as np
import logging
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtGui import QPixmap
from datetime import datetime

# gstreamer_pipeline returns a GStreamer pipeline for capturing from the CSI camera
# Flip the image by setting the flip_method (most common values: 0 and 2)
# display_width and display_height determine the size of each camera pane in the window on the screen
#Supported resolutions in case of CSI Camera
#  (2) : 640x480
#  (3) : 1280x720
#  (4) : 1920x1080
#  (5) : 2104x1560
#  (6) : 2592x1944
#  (7) : 2616x1472
#  (8) : 3840x2160
#  (9) : 3896x2192
#  (10): 4208x3120
#  (11): 5632x3168
#  (12): 5632x4224

class CSI_Camera:

    def __init__ (self) :
        # Initialize instance variables
        # OpenCV video capture element
        self.video_capture = None
        # The last captured image from the camera
        self.frame = None
        self.grabbed = False
        # The thread where the video capture runs
        self.read_thread = None
        self.read_lock = threading.Lock()
        self.running = False
        self.takepic = threading.Event()
        self.sensor_id = 0

    def startCamera(self, id):
        self.sensor_id = id
        print(self.gstreamer_pipeline_3(
                sensor_id=id,
            ))
        self.open(
            self.gstreamer_pipeline_3(
                sensor_id=id,
            )
        )
        self.start()

    def IsOpen(self):
        return (self.video_capture != None) and self.video_capture.IsOpened()

    def open(self, gstreamer_pipeline_string):
        try:
            self.video_capture = cv2.VideoCapture(
                gstreamer_pipeline_string, cv2.CAP_GSTREAMER
            )
            
        except RuntimeError:
            self.video_capture = None
            print("Unable to open camera")
            print("Pipeline: " + gstreamer_pipeline_string)
            return
        # Grab the first frame to start the video capturing
        self.grabbed, self.frame = self.video_capture.read()

    def close(self):
        self.stop()
        self.release()

    def start(self):
        if self.running:
            print('Video capturing is already running')
            return None
        # create a thread to read the camera image
        if self.video_capture != None:
            self.running=True
            self.read_thread = threading.Thread(target=self.updateCamera)
            self.read_thread.start()
        return self

    def stop(self):
        self.running=False
        self.read_thread.join()

    def updateCamera(self):
        # This is the thread to read images from the camera
        while self.running:
            try:
                grabbed, frame = self.video_capture.read()
                if not grabbed:
                    continue

                #cv2.imwrite("/tmp/ramdisk/ph_%s.jpg" % datetime.now().strftime('%Y%m%d%H%M%S.%f'), img1, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
                print("recv: " + datetime.now().strftime('%Y%m%d%H%M%S.%f'))
                if self.takepic.is_set():
                    img = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_I420)
                    #img=cv2.resize(img2, (580,720))
                    img1 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                    image = Image.fromarray(img1)
                    image.save("/tmp/ramdisk/phoneimage_%d.jpg" % self.sensor_id, quality=100)
                    #cv2.imwrite("/tmp/ramdisk/phoneimage_%d.jpg" % self.sensor_id, frame, [int(cv2.IMWRITE_JPEG_QUALITY), 100])
                    print("save image to file " + datetime.now().strftime('%Y%m%d%H%M%S.%f'))
                    self.takepic.clear()
                
                if self.read_lock.acquire(False):
                    self.grabbed=grabbed
                    self.frame=frame
                    self.read_lock.release()

                # with self.read_lock:
                #     self.grabbed=grabbed
                #     self.frame=frame
            except RuntimeError:
                print("Could not read image from camera")
        # FIX ME - stop and cleanup thread
        # Something bad happened
        

    def read(self):
        frame = None
        with self.read_lock:
            frame=self.frame
        img2 = cv2.cvtColor(frame, cv2.COLOR_YUV2BGR_I420)
        img=cv2.resize(img2, (580,720))
        img1 = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(img1)
        imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
        #print("from: "+ datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
        frame = QPixmap.fromImage(imageq) #.scaledToHeight(720)
        #print("end: "+ datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
        grabbed=self.grabbed
        return grabbed, frame

    def release(self):
        if self.video_capture != None:
            self.video_capture.release()
            self.video_capture = None
        # Now kill the thread
        if self.read_thread != None:
            self.read_thread.join()

    # Currently there are setting frame rate on CSI Camera on Nano through gstreamer
    # Here we directly select sensor_mode 8 (3840x2160, 59.9999 fps) 5) : 2104x1560
    #gstreamer_pipeline(flip_method=0, capture_height=2464, capture_width=3280, framerate=10, display_height=2464, display_width=3280)
    def gstreamer_pipeline(self,
        sensor_id=0,
        capture_width=3264,
        capture_height=2464,
        display_width=3264,
        display_height=2464,
        framerate=21,
        flip_method=0,
    ):
        return (
            "nvarguscamerasrc sensor-id=%d ! "
            "video/x-raw(memory:NVMM), "
            "width=(int)%d, height=(int)%d, "
            "format=(string)NV12, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)RGBA !"
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
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

    
    def gstreamer_pipeline_2(self,
        sensor_id=0,
        capture_width=2464,
        capture_height=3280,
        display_width=2464,
        display_height=3280,
        framerate=10,
        flip_method=1,
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

    def gstreamer_pipeline_3(self,
        sensor_id=0,
        capture_width=2464,
        capture_height=3280,
        display_width=2464,
        display_height=3280,
        framerate=10,
        flip_method=1,
    ):
        return (
            "nvarguscamerasrc exposurecompensation=1 sensor-id=%d ! "
            "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, format=(string)NV12, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)I420 ! "
            "appsink"
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

        '''
        return(
            "nvarguscamerasrc sensor-id=%d ! "
            "video/x-raw(memory:NVMM), "
            "width=(int)%d, height=(int)%d, "
            "format=(string)NV12, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=0 ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
            % (
                sensor_id,
                capture_width,
                capture_height,
                framerate,
                capture_width,
                capture_height,
            )
        )

        
        return (
            "nvarguscamerasrc sensor-id=%d sensor-mode=%d ! "
            "video/x-raw(memory:NVMM), "
            "width=(int)%d, height=(int)%d, "
            "format=(string)NV12, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
            % (
                sensor_id,
                sensor_mode,
                capture_width,
                capture_height,
                framerate,
                flip_method,
                display_width,
                display_height,
            )
        )
        '''
    def gstreamer_pipeline_4(self,
        sensor_id=0,
        capture_width=2464,
        capture_height=3280,
        display_width=2464,
        display_height=3280,
        framerate=21,
        flip_method=1,
    ):
        return (
            "nvarguscamerasrc sensor-id=%d ! "
            "video/x-raw(memory:NVMM), "
            "width=(int)%d, height=(int)%d, "
            "format=(string)NV12, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)RGBA !"
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
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