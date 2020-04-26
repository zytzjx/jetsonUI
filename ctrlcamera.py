import picamera
import io
import os
import RPi.GPIO as gp
from datetime import datetime

class CameraControl(object):
    def __init__(self):
        gp.setwarnings(False)
        gp.setmode(gp.BOARD)

        gp.setup(7, gp.OUT)
        gp.setup(11, gp.OUT)
        gp.setup(12, gp.OUT)

        gp.setup(15, gp.OUT)
        gp.setup(16, gp.OUT)
        gp.setup(21, gp.OUT)
        gp.setup(22, gp.OUT)

        gp.output(11, True)
        gp.output(12, True)
        gp.output(15, True)
        gp.output(16, True)
        gp.output(21, True)
        gp.output(22, True)
        self.camera = picamera.PiCamera()
        self._startnow = self._endnow = datetime.now()

    def IsTimeout(self):
        if self._startnow == self._endnow:
            t = datetime.now()
            return (t - self._startnow).microsecond()>1500
        return False

    def capture(filename):
        cmd = 'raspistill -ISO 50 -n -t 50 -o "%s"' % filename
        os.system(cmd)


    def _captureimage(self, filename):
        self._startnow = self._endnow = datetime.now()       
        self.camera.resolution = (3280, 2464) #(2592, 1944)
        self.camera.framerate = 15
        self.camera.brightness = 70
        #camera.image_effect = 'colorswap'
        #camera.exposure_mode = 'beach'
        #camera.awb_mode = 'sunlight'
        #imagename = "dummy_{0}.jpg".format(cam)  
        self.camera.capture(filename)  
        self._endnow = datetime.now()      

    def CaptureA(self, filename):
        i2c = "i2cset -y 0 0x70 0x00 0x04"
        os.system(i2c)
        gp.output(7, False)
        gp.output(11, False)
        gp.output(12, True)
        self._captureimage(filename)

    def CaptureB(self, filename):
        i2c = "i2cset -y 0 0x70 0x00 0x05"
        os.system(i2c)
        gp.output(7, True)
        gp.output(11, False)
        gp.output(12, True)
        self._captureimage(filename)        

    def CaptureC(self, filename):
        i2c = "i2cset -y 0 0x70 0x00 0x06"
        os.system(i2c)
        gp.output(7, False)
        gp.output(11, True)
        gp.output(12, False)
        self._captureimage(filename)        

    def Close(self):
        gp.output(7, False)
        gp.output(11, False)
        gp.output(12, True)