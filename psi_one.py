#!/usr/bin/env python3
import sys
import os
import io
import time
import picamera
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLineEdit)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent
from PyQt5.uic import loadUi
import logging
import settings
from settings import Settings
import ImageLabel
import json
import threading

from  serialstatus import FDProtocol
import serial
from xmlrpc.client import ServerProxy
import xmlrpc.client


files = []

#CURSOR_NEW = QtGui.QCursor(QtGui.QPixmap('cursor.png'))

def listImages(path):
#path = 'c:\\projects\\hc2\\'
    # r=root, d=directories, f = files
    for r, _, f in os.walk(path):
        for file in f:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                files.append(os.path.join(r, file))

class StatusCheckThread(QThread):
#https://kushaldas.in/posts/pyqt5-thread-example.html
    def __init__(self):
        QThread.__init__(self)
        self.serialport = "/dev/ttyUSB0"
        self.exit_event = threading.Event()

    # run method gets called when we start the thread
    def run(self):
        ser = serial.serial_for_url('alt://{}'.format(self.serialport), baudrate=9600, timeout=1)
    #ser = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=1)
        status=-1
        with serial.threaded.ReaderThread(ser, FDProtocol) as statusser:
            while not self.exit_event.is_set():
                if statusser.proximityStatus and not statusser.ultraSonicStatus:
                    if status!=1:
                        status=1
                        #do task start
                elif not statusser.proximityStatus:
                    if status!=2:
                        status=2
                        #start preview
                elif statusser.ultraSonicStatus:
                    if status != 2:
                        status = 2
            time.sleep(0.05)



class UISettings(QDialog):
    """Settings dialog widget
    """
    index = 0
    w = 0
    h = 0
    #filepath=""
    pixmap = None
    resized = pyqtSignal()
    def __init__(self, parent=None):
        super(UISettings, self).__init__()
        loadUi('psi_auto.ui', self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.changeStyle('Fusion')
        self.pbClose.clicked.connect(self.closeEvent)
        self.pbImageChange.clicked.connect(self.on_click)
        self.pbImageChangeDown.clicked.connect(self.on_click)
        self.pbStart.clicked.connect(self.on_startclick)
        self.updateProfile()
        self.resized.connect(self.someFunction)
        self.pbSetting.clicked.connect(self.on_settingclick)
        self.checkBox.stateChanged.connect(self.btnstate)
        self.tabWidget.currentChanged.connect(self.on_CameraChange)
        self.leProfile.hide()
        self.previewEvent = threading.Event()
        self.setStyleSheet('''
        QPushButton{background-color:rgba(255,178,0,50%);
            color: white;   
            border-radius: 10px;  
            border: 2px groove gray; 
            border-style: outset;}
		QPushButton:hover{background-color:white; 
            color: black;}
		QPushButton:pressed{background-color:rgb(85, 170, 255); 
            border-style: inset; }
        QWidget#Dialog{
            background:gray;
            border-top:1px solid white;
            border-bottom:1px solid white;
            border-left:1px solid white;
            border-top-left-radius:10px;
            border-bottom-left-radius:10px;
        }''')

        self.config=settings.DEFAULTCONFIG

        self.serialThread = StatusCheckThread()
        self.serialThread.start()

        self.threadPreview=None

        #self.on_CameraChange()
        #self.setWindowOpacity(0.5) 
        #self.setAttribute(Qt.WA_TranslucentBackground) 

        #self.resize(800, 600) 
    #def mouseMoveEvent(self, evt: QMouseEvent) -> None:
    #    logging.info(str(evt.pos().x())+"=="+str(evt.pos().y())) 
    #    super(UISettings, self).mouseMoveEvent(evt)

    #def mousePressEvent(self, evt: QMouseEvent) -> None:
    #    logging.info(str(evt.pos().x())+"=>"+str(evt.pos().y())) 
    #    super(UISettings, self).mousePressEvent(evt)

    def createprofiledirstruct(self, profiename):
        if profiename == '':
            return False
        
        if os.path.isfile('config.json'):
            with open('config.json') as json_file:
                self.config = json.load(json_file)

        pathleft = os.path.join(self.config["profilepath"], profiename, "left")
        pathtop = os.path.join(self.config["profilepath"], profiename, "top")
        pathright = os.path.join(self.config["profilepath"], profiename, "right")
        mode = 0o777
        os.makedirs(pathleft, mode, True) 
        os.makedirs(pathtop, mode, True) 
        os.makedirs(pathright, mode, True) 

    def closeEvent(self, event):
        self._shutdown()
        self.serialThread.exit_event.set()
        self.close()


    def resizeEvent(self, event):
        self.resized.emit()
        return super(UISettings, self).resizeEvent(event)

    def someFunction(self):
        logging.info(str(self.width())+"X"+str(self.height()))   

    def changeStyle(self, styleName):
        QApplication.setStyle(QStyleFactory.create(styleName))
        QApplication.setPalette(QApplication.style().standardPalette())

    def updateProfile(self):
        curpath=os.path.abspath(os.path.dirname(sys.argv[0]))
        profilepath=os.path.join(curpath,"profiles")
        self.comboBox.addItems([name for name in os.listdir(profilepath) if os.path.isdir(os.path.join(profilepath, name))])
        
 
    def loadimage(self,filepath):
        pixmap = QPixmap(filepath)
        self.imageTop.setPixmap(pixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    
    def loadimageA(self):
        #self.index+=1
        filepath=files[self.index%len(files)]
        self.loadimage(filepath)

    def DrawImage(self, x, y, clr = Qt.red):
        # convert image file into pixmap
        #pixmap = QPixmap(self.filepath)
        if self.pixmap == None:
            return
        # create painter instance with pixmap
        painterInstance = QPainter(self.pixmap)

        # set rectangle color and thickness
        penRectangle = QPen(clr)
        penRectangle.setWidth(3)

        # draw rectangle on painter
        painterInstance.setPen(penRectangle)
        painterInstance.drawEllipse(x,y,25,25)

        # set pixmap onto the label widget
        self.imageTop.setPixmap(self.pixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))    
        painterInstance.end()


    def PreviewCamera(self):
        # Create the in-memory stream
        stream = io.BytesIO()
        with picamera.PiCamera() as camera:
            camera.start_preview()
            time.sleep(1)
            camera.capture(stream, format='jpeg')
            camera.stop_preview()
        # "Rewind" the stream to the beginning so we can read its content
        stream.seek(0)
        image = Image.open(stream)
        imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
        #qimage = QImage(imageq)
        #pixmap = QPixmap(qimage)
        pixmap = QPixmap.fromImage(imageq)
        self.imageTop.imagepixmap = pixmap
        #self.lblImage.setPixmap(self.pixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))   


    @pyqtSlot()
    def btnstate(self):
        if self.sender().isChecked():
            self.imageTop.isProfile = True
            self.imageLeft.isProfile = True
            self.imageRight.isProfile = True
            self.leProfile.show()
            self.comboBox.hide()
        else:
            self.imageTop.isProfile = False
            self.imageLeft.isProfile = False
            self.imageRight.isProfile = False
            self.leProfile.hide()
            self.comboBox.show()

    def takephotoshow(self, cameraindex, picname, profilename):
        #self.takephoto           

        if ImageLabel.CAMERA.TOP==cameraindex:
            self.imageTop.profilerootpath = self.config["profilepath"]
            self.imageTop.setImageScale()
            self.imageTop.SetProfile(profilename, "top.jpg")
            self.pixmap = QPixmap(picname)
            logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
            self.imageTop.imagepixmap = self.pixmap
            self.imageTop.SetCamera(ImageLabel.CAMERA.TOP)
            #self.imageTop.SetProfile("iphone6s_top_1","iphone6s_top_1.jpg")
        elif ImageLabel.CAMERA.LEFT==cameraindex:
            self.imageLeft.profilerootpath = self.config["profilepath"]
            self.imageLeft.setImageScale()
            self.imageLeft.SetProfile(profilename, "left.jpg")
            self.pixmap = QPixmap(picname)
            logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
            self.imageLeft.imagepixmap = self.pixmap
            self.imageLeft.SetCamera(ImageLabel.CAMERA.LEFT)
            #self.imageTop.SetProfile("iphone6s_top_2","iphone6s_top_2.jpg")
        else:
            self.imageRight.profilerootpath = self.config["profilepath"]
            self.imageRight.setImageScale()
            self.imageRight.SetProfile(profilename, "right.jpg")
            self.pixmap = QPixmap(picname)
            logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
            self.imageRight.imagepixmap = self.pixmap
            self.imageRight.SetCamera(ImageLabel.CAMERA.RIGHT)


    @pyqtSlot()
    def on_CameraChange(self):
        if self.tabWidget.currentIndex()==0:
            self.imageTop.profilerootpath = self.config["profilepath"]
            self.imageTop.setImageScale()
            self.imageTop.SetProfile(self.leProfile.text(), "top.jpg")
            self.pixmap = QPixmap('iphone6s_3_s1.jpg')
            logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
            self.imageTop.imagepixmap = self.pixmap
            self.imageTop.SetCamera(ImageLabel.CAMERA.TOP)
            self.imageTop.SetProfile("iphone6s_top_1","iphone6s_top_1.jpg")
        elif self.tabWidget.currentIndex()==1:
            self.imageLeft.profilerootpath = self.config["profilepath"]
            self.imageLeft.setImageScale()
            self.imageLeft.SetProfile(self.leProfile.text(), "left.jpg")
            self.pixmap = QPixmap('/home/pi/Desktop/pyUI/curimage.jpg')
            logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
            self.imageLeft.imagepixmap = self.pixmap
            self.imageLeft.SetCamera(ImageLabel.CAMERA.LEFT)
            self.imageTop.SetProfile("iphone6s_top_2","iphone6s_top_2.jpg")
        else:
            self.imageRight.profilerootpath = self.config["profilepath"]
            self.imageRight.setImageScale()
            self.imageRight.SetProfile(self.leProfile.text(), "right.jpg")
            self.pixmap = QPixmap('/home/pi/Desktop/pyUI/iphone6s_3_s1.jpg')
            logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
            self.imageRight.imagepixmap = self.pixmap
            self.imageRight.SetCamera(ImageLabel.CAMERA.RIGHT)


    @pyqtSlot()
    def on_settingclick(self):
        dlg = Settings(self)
        if dlg.exec_():
            print("Success!")
        else:
            print("Cancel!")        

    @pyqtSlot()
    def on_click(self):
        sender = self.sender()
        clickevent = sender.text()
        if clickevent == u'Image UP':
            self.previewEvent.set() 
        else:
            self.OnPreview()

    @pyqtSlot()
    def on_startclick(self):
        if self.leProfile.text()=="" and self.checkBox.isChecked():
            error_dialog = QtWidgets.QErrorMessage(self)
            error_dialog.showMessage('Oh no! Profile name is empty.') 
            return             
        
        self.createprofiledirstruct(self.leProfile.text())
        self.on_CameraChange()
        #self.imageTop.setImageScale()

        #self.pixmap = QPixmap('/home/pi/Desktop/pyUI/iphone6s_3_s1.jpg')
        #logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
        #self.imageTop.imagepixmap = self.pixmap
        return

        filepath = '/home/pi/Desktop/pyUI/curimage.jpg'
        with picamera.PiCamera() as camera:
            camera.resolution = (3280, 2464)
            camera.start_preview()
            camera.capture(filepath)
            camera.stop_preview()   

        self.pixmap = QPixmap(filepath)
        logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
        self.imageTop.imagepixmap = self.pixmap
        #self.lblImage.setPixmap(self.pixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation)) 
        #logging.info(str(self.lblImage.pixmap().width())+"X"+str(self.lblImage.pixmap().height()))
        #logging.info(str(self.w)+"X"+str(self.h))   
    
    def _shutdown(self):
        client = ServerProxy("http://localhost:8888", allow_none=True)
        client.CloseServer()


    def _GetImageShow(self):
        #from PIL import Image
        #import urllib.request

        client = ServerProxy("http://localhost:8888", allow_none=True)
        #url = 'http://127.0.0.1:5000/startpause'
        #urllib.request.urlopen(url)
        logging.info(client.startpause())
        time.sleep(0.1)
        while True:
            #url = 'http://127.0.0.1:5000/preview'
            data = client.preview().data
            image = Image.open(io.BytesIO(data))
            imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
            pixmap = QPixmap.fromImage(imageq)
            self.imageTop.imagepixmap = pixmap
            if self.previewEvent.is_set():
                self.previewEvent.clear()
                #url = 'http://127.0.0.1:5000/startpause'
                #urllib.request.urlopen(url)
                client.startpause()
                break

    def OnPreview(self):
        if self.threadPreview==None or not self.threadPreview.is_alive():
            self.threadPreview= threading.Thread(target=self._GetImageShow)
            self.threadPreview.start()
 
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    app = QApplication(sys.argv)
    #listImages('C:/Users/jefferyz/Desktop/pictures/')
    window = UISettings()
 
    window.show()
    window.showFullScreen()
     
    logging.info(str(window.width())+"X"+str(window.height()))   
    sys.exit(app.exec_())
