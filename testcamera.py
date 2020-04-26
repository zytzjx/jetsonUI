from datetime import datetime
import picamera
import RPi.GPIO as gp
import os
import time

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
#camera = picamera.PiCamera()


def main():
    while True:
        print(datetime.now().strftime("%H:%M:%S.%f"),"Start testing the camera A")
        i2c = "i2cset -y 1 0x70 0x00 0x04"
        os.system(i2c)
        gp.output(7, False)
        gp.output(11, False)
        gp.output(12, True)
        capture(1)
        print(datetime.now().strftime("%H:%M:%S.%f"),"Start testing the camera B")
        i2c = "i2cset -y 1 0x70 0x00 0x05"
        os.system(i2c)
        gp.output(7, True)
        gp.output(11, False)
        gp.output(12, True)
        capture(2)
        print(datetime.now().strftime("%H:%M:%S.%f"),"Start testing the camera C")
        i2c = "i2cset -y 1 0x70 0x00 0x06"
        os.system(i2c)
        gp.output(7, False)
        gp.output(11, True)
        gp.output(12, False)
        capture(3)
        #print"Start testing the camera D"
        #i2c = "i2cset -y 1 0x70 0x00 0x07"
        #os.system(i2c)
        #gp.output(7, True)
        #gp.output(11, True)
        #gp.output(12, False)
        #capture(4)
        print(datetime.now().strftime("%H:%M:%S.%f"),"ending, sleep 2s")
        time.sleep(2)

def capture(cam):
    cmd = "raspistill -t 50 -o capture_%d.jpg" % cam
    os.system(cmd)

def capturepy(cam):
    camera.resolution = (3280, 2464) #(2592, 1944)
    camera.framerate = 15
    camera.brightness = 70
    #camera.image_effect = 'colorswap'
    #camera.exposure_mode = 'beach'
    #camera.awb_mode = 'sunlight'
    imagename = "dummy_{0}.jpg".format(cam)  
   	#camera.capture(imagename)

if __name__ == "__main__":
    main()

    gp.output(7, False)
    gp.output(11, False)
    gp.output(12, True)
