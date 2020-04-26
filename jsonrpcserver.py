#!/usr/bin/env python
# coding: utf-8
 
#import pyjsonrpc
from gevent.server import StreamServer
from mprpc import RPCServer
from datetime import datetime
import RPi.GPIO as gp
import os
import sys
import time 
import shutil
import threading

from PyQt5.QtWidgets import (QApplication, QDialog)
from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal,QPoint, QRect
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent
 
import profiledata

class RequestHandler(RPCServer):#pyjsonrpc.HttpRequestHandler):
    def __init__(self):
        RPCServer.__init__(self)
        self.imageresult0={}
        self.imageresult1={}
        self.imageresult2={}
        self.profilename=""
        self.rootprofielpath=""
        self._profilepath=""
        self.screwW = 24
        self.screwH = 24
        self._imagepixmapback = None
        self._curIndex=0
        self._indexscrew = 0

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
        return self._profilepath

    def CloseServer(self):
        server.stop()

    def _callyanfunction(self, index):
        print('callyanfunction:' +self.profilename)
        pass

    def _startdetectthread(self, index):
        t1 = threading.Thread(target=self._callyanfunction, args=(index,))
        t1.start()

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
    
    #@pyjsonrpc.rpcmethod
    def Uninit(self):
        gp.output(7, False)
        gp.output(11, False)
        gp.output(12, True)

    def _DirSub(self, argument):
        switcher = {
            1: "left",
            0: "top",
            2: "right",
        }
        return switcher.get(argument, "Invalid")

    def capture(self, cam, IsDetect=True):
        cmd = "raspistill -ISO 50 -n -t 50 -o /tmp/ramdisk/phoneimage_%d.jpg" % cam
        os.system(cmd)
        if not IsDetect:
            shutil.copyfile("/tmp/ramdisk/phoneimage_%d.jpg" % cam, os.path.join(self._profilepath, self._DirSub(cam), self.profilename+".jpg"))
        #return QPixmap("/tmp/ramdisk/phoneimage_%d.jpg" % cam)
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
        if index==0:
            return self.imageresult0
        elif index==1:
            return self.imageresult1
        elif index==2:
            return self.imageresult2
        else:
            return '{"aa":"bb"}'

 
if __name__ == "__main__": 
    # Threading HTTP-Server
    #http_server = pyjsonrpc.ThreadingHttpServer(
    #    server_address = ('0.0.0.0', 8080),
    #    RequestHandlerClass = RequestHandler
    #)
    app = QApplication(sys.argv)
    handler = RequestHandler()
    handler.Init()
    server = StreamServer(('0.0.0.0', 8080), handler)
    print("Starting HTTP server ...")
    print("URL: http://+:8080")
    #server.serve_forever()

    try:
        #http_server.serve_forever()
        server.serve_forever()
    except KeyboardInterrupt:
        #http_server.shutdown()
        server.stop()

    handler.Uninit()

    #sys.exit(app.exec_())