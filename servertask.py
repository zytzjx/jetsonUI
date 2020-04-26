# _*_ coding:utf-8 _*_

from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn
import xmlrpc.client
from datetime import datetime
import RPi.GPIO as gp
import os
import sys
import time 
import shutil
import threading

import picamera
import io
from PIL import Image
import logging

from PyQt5.QtWidgets import (QApplication, QDialog)
from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal,QPoint, QRect
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent
 
import profiledata
import testScrew

import json
import subprocess


class ThreadXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass


class RequestHandler():#pyjsonrpc.HttpRequestHandler):
    def __init__(self):
        #RPCServer.__init__(self)
        #self.imageresult0=[]
        #self.imageresult1=[]
        #self.imageresult2=[]
        self.imageresults=[[],[],[]]
        self.profilename=""
        self.rootprofielpath=""
        self._profilepath=""
        self.screwW = 24
        self.screwH = 24
        self._imagepixmapback = None
        self._curIndex=0
        self._indexscrew = 0

        self.quit_event = threading.Event()
        self.pause_event = threading.Event()
        self.save_image_event = threading.Event()
        self.save_complete_event = threading.Event()
        self.image_ready = io.BytesIO()
        self.lockyan=threading.Lock()
        self.yanthreads=[]
        logging.basicConfig(stream=sys.stdout, level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self._config={}
        self._tpreview =None
        self.IsPreviewing=False

    def setConfig(self, sconfig):
        if not (sconfig is None or sconfig==""):
            self._config=json.loads(sconfig)

    def _setactivecamera(self, index=0):
        if index==0:
            print(datetime.now().strftime("%H:%M:%S.%f"),"Start testing the camera A")
            i2c = "i2cset -y 1 0x70 0x00 0x04"
            os.system(i2c)
            gp.output(7, False)
            gp.output(11, False)
            gp.output(12, True)

    def _preview(self):
        while True:
            logging.info("preview: thread is starting...")
            self.IsPreviewing=False
            self.pause_event.wait()
            self.IsPreviewing=True
            self.pause_event.clear()
            if self.quit_event.is_set():
                self.IsPreviewing=False
                break
            self._setactivecamera(0)
            stream = io.BytesIO()
            with picamera.PiCamera() as camera:
                camera.ISO = 50
                camera.resolution=(640,480)
                #camera.start_preview()
                #time.sleep(2)
                for foo in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
                    stream.seek(0)
                    self.IsPreviewing=True
                    image = Image.open(stream)
                    if self.save_image_event.is_set():
                        # with open("foo.jpg", "w") as f:                
                        #     image.save(f)
                        if self.image_ready is None or self.image_ready.closed:
                            self.image_ready = io.BytesIO()
                        else:
                            self.image_ready.seek(0)
                            self.image_ready.truncate()
                        image.save(self.image_ready, format='JPEG')
                        self.save_complete_event.set()
                        self.save_image_event.clear()
                        
                    stream.seek(0)
                    stream.truncate()
                    if self.pause_event.is_set() or self.quit_event.is_set():
                        self.pause_event.clear()
                        self.IsPreviewing=False
                        break

            if self.quit_event.is_set():
                self.IsPreviewing=False
                break
        logging.info("preview: thread is terminated")

    def preview(self):
        self.save_image_event.set()
        self.save_complete_event.wait()
        self.save_complete_event.clear()
        self.image_ready.seek(0)
        data = self.image_ready.read()
        return xmlrpc.client.Binary(data)#send_file(image_ready, mimetype='image/jpeg')

    def startpause(self, pause=True):
        if pause and self.IsPreviewing:
            print("pause:True, IsPreviewing:True")
            self.pause_event.set()
        elif not pause and not self.IsPreviewing:
            print("pause:False, IsPreviewing:False")
            self.pause_event.set()
            while not self.IsPreviewing:
                time.sleep(0.01)
        else:
            print(str(pause)+":"+str(self.IsPreviewing))
            pass
        return "OK"


    def _shutdownpreview(self):
        self.quit_event.set()
        self.pause_event.set()        
        return 'Server shutting down...'

    def cleanprofileparam(self):
        self._imagepixmapback = None
        self._curIndex=0
        self._indexscrew = 0

    #@pyjsonrpc.rpcmethod
    def add(self, a, b):
        """Test method"""
        return a + b

    def profilepath(self, rpp, pn):
        #global profilename, _profilepath
        if rpp and rpp!="":
            self.rootprofielpath=rpp
        if pn and pn!="":
            self.profilename=pn

        self._profilepath= os.path.join(self.rootprofielpath, self.profilename)
        pathleft = os.path.join(self._profilepath, "left")
        pathtop = os.path.join(self._profilepath, "top")
        pathright = os.path.join(self._profilepath, "right")
        mode = 0o777
        os.makedirs(pathleft, mode, True) 
        os.makedirs(pathtop, mode, True) 
        os.makedirs(pathright, mode, True) 

        return self._profilepath

    def CloseServer(self):
        self._shutdownpreview()       
        server.shutdown()

    def SyncRamdisks(self):
    #rsync -avzP --delete pi@192.168.1.12:/home/pi/Desktop/pyUI/profiles /home/pi/Desktop/pyui/profiles/
        logging.info(datetime.now().strftime("%H:%M:%S.%f")+"   call rsync++")
        subprocess.call(["rsync", "-avzP", '--delete', '/tmp/ramdisk/', "pi@192.168.1.16:/tmp/ramdisk"])
        logging.info(datetime.now().strftime("%H:%M:%S.%f")+"   call rsync--")


    def _callyanfunction(self, index):
        print('callyanfunction:' +self.profilename)
        txtfilename=os.path.join(self._profilepath, self._DirSub(index), self.profilename+".txt")
        smplfilename=os.path.join(self._profilepath, self._DirSub(index), self.profilename+".jpg")
        logging.info(txtfilename)
        logging.info(smplfilename)
        if os.path.exists(txtfilename) and os.path.exists(smplfilename):
            self.lockyan.acquire()
            logging.info(datetime.now().strftime("%H:%M:%S.%f")+"   *testScrews**")
            try:
                '''
                resultjon = "/tmp/ramdisk/result_%d.json" % index
                cmdline=' python3 testScrew.py -txtfilename "{0}" -jpgfilename "{1}" -testImageName {2} -result {3}'.format(
                    txtfilename, smplfilename, "/tmp/ramdisk/phoneimage_%d.jpg" % index, resultjon
                )
                logging.info(cmdline)
                #os.system(cmdline)
                subprocess.call(["python3", "testScrew.py", '-txtfilename', txtfilename, '-jpgfilename', smplfilename, '-testImageName', "/tmp/ramdisk/phoneimage_%d.jpg" % index, '-result', resultjon])
                logging.info(datetime.now().strftime("%H:%M:%S.%f")+"   -testScrews--")

                '''
                dataresult = testScrew.testScrews(
                    txtfilename, 
                    smplfilename, 
                    "/tmp/ramdisk/phoneimage_%d.jpg" % index)
                self.imageresults[index] = dataresult
                '''
                if os.path.exists(resultjon):
                    with open(resultjon) as json_file:
                        dataresult = json.load(json_file)                    
                        self.imageresults[index] = dataresult
                else:
                    self.imageresults[index] = []
                '''
            except :
                self.imageresults[index] = []
                pass
            
            logging.info(datetime.now().strftime("%H:%M:%S.%f")+"   -testScrews end--")
            self.lockyan.release()
            print(self.imageresults[index])

    def _startdetectthread(self, index):
        t1 = threading.Thread(target=self._callyanfunction, args=(index,))
        t1.start()
        self.yanthreads.append(t1)

    def _fileprechar(self, argument):
        switcher = {
            1: "L",
            0: "T",
            2: "R",
        }
        return switcher.get(argument, "Invalid")

    def _savescrew(self, index, pt):
        #h = a-b if a>b else a+b
        x = pt.x()-self.screwW if pt.x()-self.screwW > 0 else 0
        y = pt.y()-self.screwH if pt.y()-self.screwH > 0 else 0
 
        x1 = pt.x() + self.screwW if pt.x() + self.screwW < self._imagepixmapback.width() else self._imagepixmapback.width()
        y1 = pt.y() + self.screwH if pt.y() + self.screwH < self._imagepixmapback.height() else self._imagepixmapback.height()
        
        currentQRect = QRect(QPoint(x,y),QPoint(x1,y1))
        cropQPixmap = self._imagepixmapback.copy(currentQRect)
        profilepath=self._profilepath
        filename = self._fileprechar(index)+str(self._indexscrew)+".png" 
        profilepath=os.path.join(profilepath, self._DirSub(index), filename)
        self._indexscrew+=1
        cropQPixmap.save(profilepath)
        screwpoint = profiledata.screw(self.profilename, filename, pt, QPoint(x,y), QPoint(x1,y1))
        #self.ProfilePoint.append(screwpoint)
        sinfo = profilepath+", "+str(x)+", "+str(x1)+", "+str(y)+", "+str(y1)
        profiletxt = os.path.join(self._profilepath, self._DirSub(index),  self.profilename+".txt")
        self._append_new_line(profiletxt, sinfo)

    def _append_new_line(self, file_name, text_to_append):
        """Append given text as a new line at the end of file"""
        # Open the file in append & read mode ('a+')
        with open(file_name, "a+") as file_object:
            # Move read cursor to the start of file.
            file_object.seek(0)
            # If file is not empty then append '\n'
            data = file_object.read(100)
            if len(data) > 0:
                file_object.write("\n")
            # Append text at the end of file
            file_object.write(text_to_append)

    def CreateSamplePoint(self, index, x, y):
        if self._imagepixmapback == None or index != self._curIndex:
            filename = "/tmp/ramdisk/phoneimage_%d.jpg" % index
            self._imagepixmapback = QPixmap(filename)
        self._savescrew(index, QPoint(x,y))

    #@pyjsonrpc.rpcmethod
    def updateProfile(self, ppath):
        if not ppath or ppath=="":
            curpath=os.path.abspath(os.path.dirname(sys.argv[0]))
            ppath=os.path.join(curpath,"profiles")
        return [name for name in os.listdir(ppath) if os.path.isdir(os.path.join(ppath, name))]


    #@pyjsonrpc.rpcmethod
    def Init(self):
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

        self._StartDaemon()
    
    #@pyjsonrpc.rpcmethod
    def Uninit(self):
        gp.output(7, False)
        gp.output(11, False)
        gp.output(12, True)

        self._shutdownpreview()

    def _DirSub(self, argument):
        switcher = {
            1: "left",
            0: "top",
            2: "right",
        }
        return switcher.get(argument, "Invalid")

    '''
    def _ChangeImageSize(self, index, scale_percent=25):
        import cv2
        cmd = "/tmp/ramdisk/phoneimage_%d.jpg" % index
        img = cv2.imread(cmd, cv2.IMREAD_UNCHANGED) 
        print('Original Dimensions : ',img.shape) 
        #scale_percent = 220 # percent of original size
        width = int(img.shape[1] * scale_percent / 100)
        height = int(img.shape[0] * scale_percent / 100)
        dim = (width, height)
        # resize image
        resized = cv2.resize(img, dim, interpolation = cv2.INTER_AREA)
        filename = "/tmp/ramdisk/compressimage_%d.jpg" % index
        cv2.imwrite(filename, img, [cv2.IMWRITE_JPEG_QUALITY, 30]) 
        return filename
    '''    

    def imageDownload(self, cam, IsDetect=True):
        cmd = "/tmp/ramdisk/phoneimage_%d.jpg" % cam
        #cmd = self._ChangeImageSize(cam)
        handle = open(cmd, 'rb')
        return xmlrpc.client.Binary(handle.read())
    
    def capture(self, cam, IsDetect=True):
        cmd = "raspistill -ISO 50 -n -t 50 -o /tmp/ramdisk/phoneimage_%d.jpg" % cam
        os.system(cmd)
        if not IsDetect:
            shutil.copyfile("/tmp/ramdisk/phoneimage_%d.jpg" % cam, os.path.join(self._profilepath, self._DirSub(cam), self.profilename+".jpg"))
        else:
            self._startdetectthread(cam)

    #@pyjsonrpc.rpcmethod
    def TakePicture(self, index, IsDetect=True):
        if index==0:
            print(datetime.now().strftime("%H:%M:%S.%f"),"Start testing the camera A")
            i2c = "i2cset -y 1 0x70 0x00 0x04"
            os.system(i2c)
            gp.output(7, False)
            gp.output(11, False)
            gp.output(12, True)
        elif index == 1:
            print(datetime.now().strftime("%H:%M:%S.%f"),"Start testing the camera B")
            i2c = "i2cset -y 1 0x70 0x00 0x05"
            os.system(i2c)
            gp.output(7, True)
            gp.output(11, False)
            gp.output(12, True)
        else:
            print(datetime.now().strftime("%H:%M:%S.%f"),"Start testing the camera C")
            i2c = "i2cset -y 1 0x70 0x00 0x06"
            os.system(i2c)
            gp.output(7, False)
            gp.output(11, True)
            gp.output(12, False)
        return self.capture(index, IsDetect)

    def ResultTest(self, index):  
        #for st in self.yanthreads:
        #    if st.isAlive():
        #        st.join()

        #self.yanthreads=[]
        if self.yanthreads[index].isAlive():
            self.yanthreads[index].join()
        data=[]     
        if index<3:
            data = self.imageresults[index]
        ss = json.dumps(data)
        print(ss)
        return ss

    def _StartDaemon(self):
        if self._tpreview is None or not self._tpreview.is_alive():
            self._tpreview = threading.Thread(target=self._preview, daemon=True)
            self._tpreview.start()


if __name__ == '__main__':
    app = QApplication([])
    server = ThreadXMLRPCServer(('0.0.0.0', 8888), allow_none=True) # 初始化
    #server.register_function(image_put, 'image_put')
    #server.register_function(image_get, 'image_get')
    handler = RequestHandler()
    handler.Init()
    server.register_instance(handler)
    print ("Listening for Client")
    #server.serve_forever() # 保持等待调用状态
    try:
        #http_server.serve_forever()
        server.serve_forever()
    except KeyboardInterrupt:
        print("Exiting")
    
    handler.Uninit()