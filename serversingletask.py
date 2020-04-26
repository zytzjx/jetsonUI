# _*_ coding:utf-8 _*_

from xmlrpc.server import SimpleXMLRPCServer
from socketserver import ThreadingMixIn
import xmlrpc.client
from datetime import datetime
#import RPi.GPIO as gp
import os
import sys
import time 
import shutil
import threading

import picamera
import io
from PIL import Image
import logging

#from PyQt5.QtWidgets import (QApplication, QDialog)
#from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal,QPoint, QRect
#from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent
from PyQt5.QtCore import QPoint, QRect

import profiledata
import testScrew
import argparse

import json
import subprocess
import myconstdef



class ThreadXMLRPCServer(ThreadingMixIn, SimpleXMLRPCServer):
    pass


class RequestHandler():#pyjsonrpc.HttpRequestHandler):
    def __init__(self):
        self.logger = logging.getLogger('PSILOG')
        self.imageresults=[[],[],[]]
        self.profilename=""
        self.rootprofielpath=""
        self._profilepath=""
        self.screwW = myconstdef.screwWidth
        self.screwH = myconstdef.screwHeight
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
        #logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        self._config={}
        self._tpreview =None
        self.IsPreviewing=False

    def setScrewSize(self, w, h):
        self.screwW = w
        self.screwH = h


    def setConfig(self, sconfig):
        if not (sconfig is None or sconfig==""):
            self._config=json.loads(sconfig)

    def _setactivecamera(self, index=0):
        if index==0:
            self.logger.info("Start testing the camera A")
            #i2c = "i2cset -y 1 0x70 0x00 0x04"
            #os.system(i2c)
            #gp.output(7, False)
            #gp.output(11, False)
            #gp.output(12, True)

    def _preview(self):
        while True:
            self.logger.info("preview: thread is starting...")
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
        self.logger.info("preview: thread is terminated")

    def preview(self):
        self.save_image_event.set()
        self.save_complete_event.wait()
        self.save_complete_event.clear()
        self.image_ready.seek(0)
        data = self.image_ready.read()
        return xmlrpc.client.Binary(data)#send_file(image_ready, mimetype='image/jpeg')

    def startpause(self, pause=True):
        if pause and self.IsPreviewing:
            self.logger.info("pause:True, IsPreviewing:True")
            self.pause_event.set()
        elif not pause and not self.IsPreviewing:
            self.logger.info("pause:False, IsPreviewing:False")
            self.pause_event.set()
            while not self.IsPreviewing:
                time.sleep(0.01)
        else:
            self.logger.info(str(pause)+":"+str(self.IsPreviewing))
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

    def profilepath(self, rpp, pn):
        #global profilename, _profilepath
        self.logger.info("call profilepath ++")
        if rpp and rpp!="":
            self.rootprofielpath=rpp
        if pn and pn!="":
            self.profilename=pn

        self._profilepath= os.path.join(self.rootprofielpath, self.profilename)
        pathleft = os.path.join(self._profilepath, "left")
        pathtop = os.path.join(self._profilepath, "top")
        pathright = os.path.join(self._profilepath, "right")
        mode = 0o777
        if not os.path.exists(pathleft):
            os.makedirs(pathleft, mode, True) 
        if not os.path.exists(pathtop):
            os.makedirs(pathtop, mode, True) 
        if not os.path.exists(pathright):
            os.makedirs(pathright, mode, True) 
        self.logger.info("call profilepath -- " + self._profilepath)
        return self._profilepath

    def CloseServer(self):
        #self._shutdownpreview()       
        server.shutdown()

    def SyncRamdisks(self):
    #rsync -avzP --delete pi@192.168.1.12:/home/pi/Desktop/pyUI/profiles /home/pi/Desktop/pyui/profiles/
        self.logger.info("call rsync++")
        subprocess.call(["rsync", "-avzP", '--delete', '/tmp/ramdisk/', "pi@192.168.1.16:/tmp/ramdisk"])
        self.logger.info(datetime.now().strftime("%H:%M:%S.%f")+"   call rsync--")


    def _callyanfunction(self, index):
        self.logger.info('callyanfunction:' +self.profilename)
        txtfilename=os.path.join(self._profilepath, self._DirSub(index), self.profilename+".txt")
        smplfilename=os.path.join(self._profilepath, self._DirSub(index), self.profilename+".jpg")
        self.logger.info(txtfilename)
        self.logger.info(smplfilename)
        if os.path.exists(txtfilename) and os.path.exists(smplfilename):
            self.lockyan.acquire()
            self.logger.info("*testScrews**")
            try:
                dataresult = testScrew.testScrews(
                    txtfilename, 
                    smplfilename, 
                    "/tmp/ramdisk/phoneimage_%d.jpg" % index)
                self.imageresults[index] = dataresult
            except :
                self.imageresults[index] = []
                pass
            
            self.logger.info("-testScrews end--")
            self.lockyan.release()
            self.logger.info(self.imageresults[index])

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
        screwLeft = int(self.screwW /2)
        screwRight = int (self.screwW - screwLeft)
        screwTop = int(self.screwH / 2)
        screwBottom = int (self.screwH - screwTop)
        x = pt.x()-screwLeft if pt.x()-screwLeft > 0 else 0
        y = pt.y()-screwTop if pt.y()-screwTop > 0 else 0
 
        width, height = self._imagepixmapback.size

        #x1 = pt.x() + self.screwW if pt.x() + self.screwW < self._imagepixmapback.width() else self._imagepixmapback.width()
        #y1 = pt.y() + self.screwH if pt.y() + self.screwH < self._imagepixmapback.height() else self._imagepixmapback.height()
        x1 = pt.x() + screwRight if pt.x() + screwRight < width else width
        y1 = pt.y() + screwBottom if pt.y() + screwBottom < height else height
        
        #currentQRect = QRect(QPoint(x,y),QPoint(x1,y1))
        cropQPixmap = self._imagepixmapback.crop((x,y,x1,y1))#.copy(currentQRect)
        print("copy image")
        profilepath=self._profilepath
        filename = self._fileprechar(index)+str(self._indexscrew)+".png" 
        profilepath=os.path.join(profilepath, self._DirSub(index), filename)
        self._indexscrew+=1
        cropQPixmap.save(profilepath)
        screwpoint = profiledata.screw(self.profilename, filename, pt, QPoint(x,y), QPoint(x1,y1))
        #self.ProfilePoint.append(screwpoint)
        sinfo = profilepath+", "+str(x)+", "+str(x1)+", "+str(y)+", "+str(y1)
        print(sinfo)
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
            self._imagepixmapback = Image.open(filename)#QPixmap(filename)
        self._savescrew(index, QPoint(x,y))

    def updateProfile(self, ppath):
        if not ppath or ppath=="":
            curpath=os.path.abspath(os.path.dirname(sys.argv[0]))
            ppath=os.path.join(curpath,"profiles")
        return [name for name in os.listdir(ppath) if os.path.isdir(os.path.join(ppath, name))]


    def _DirSub(self, argument):
        switcher = {
            1: "left",
            0: "top",
            2: "right",
        }
        return switcher.get(argument, "Invalid")

    def imageDownload(self, cam, IsDetect=True):
        cmd = "/tmp/ramdisk/phoneimage_%d.jpg" % cam
        #cmd = self._ChangeImageSize(cam)
        handle = open(cmd, 'rb')
        return xmlrpc.client.Binary(handle.read())
    
    def capture(self, cam, IsDetect=True):
        cmd = "raspistill -vf -hf -ISO 50 -n -t 50 -o /tmp/ramdisk/phoneimage_%d.jpg" % cam
        if cam ==0:
            cmd = "raspistill -ISO 50 -n -t 50 -o /tmp/ramdisk/phoneimage_%d.jpg" % cam
        os.system(cmd)
        if not IsDetect:
            shutil.copyfile("/tmp/ramdisk/phoneimage_%d.jpg" % cam, os.path.join(self._profilepath, self._DirSub(cam), self.profilename+".jpg"))
        else:
            #self._startdetectthread(cam)
            self._callyanfunction(cam)

    #@pyjsonrpc.rpcmethod
    def TakePicture(self, index, IsDetect=True):
        if index==0:
            self.logger.info("Start testing the camera A")
        elif index == 1:
            self.logger.info("Start testing the camera B")
        else:
            self.logger.info("Start testing the camera C")
        return self.capture(index, IsDetect)

    def ResultTest(self, index):  
        #for st in self.yanthreads:
        #    if st.isAlive():
        #        st.join()

        #self.yanthreads=[]
        #if self.yanthreads[index].isAlive():
        #    self.yanthreads[index].join()
        data=[]     
        print(self.imageresults)
        if index<3:
            data = self.imageresults[index]
        ss = json.dumps(data)
        self.logger.info(ss)
        return ss

    def StartDaemon(self):
        if self._tpreview is None or not self._tpreview.is_alive():
            self._tpreview = threading.Thread(target=self._preview, daemon=True)
            self._tpreview.start()

    def RemoveProfile(self, profile):
        dirPath=os.path.join(self.rootprofielpath, profile)
        try:
            shutil.rmtree(dirPath)
        except:
            self.logger.error('Error while deleting directory')  

    def RenameProfile(self, source, target):
        dirPath=os.path.join(self.rootprofielpath, source)
        dirPath1=os.path.join(self.rootprofielpath, target)
        try:
            os.rename(dirPath, dirPath1)
        except:
            self.logger.error('Error  renaming directory')  

def CreateLog():
    import logging
    from logging.handlers import RotatingFileHandler

    formatter = logging.Formatter('%(asctime)s-%(levelname)s-%(funcName)s(%(lineno)d) %(message)s')

    logFile = '/tmp/ramdisk/psi.log'
    handler = RotatingFileHandler(logFile, mode='a', maxBytes=1*1024*1024, 
                                    backupCount=500, encoding=None, delay=False)
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    logger = logging.getLogger('PSILOG')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger

if __name__ == '__main__':
    #app = QApplication([])
    logger = CreateLog()
    ap = argparse.ArgumentParser()
    ap.add_argument("-style", "-style which camera[top left right]", type=str, required=True,
    	help="which camera")
    args = vars(ap.parse_args())

    server = ThreadXMLRPCServer(('0.0.0.0', 8888), allow_none=True) # 初始化
    handler = RequestHandler()
    server.register_instance(handler)
    if args["style"] == 'top':
        handler.StartDaemon()
    logger.info("Listening for Client")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.error("Exiting keyinterrupt")
    