#!/usr/bin/env python3
import sys
import os
import io
import time
import picamera
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal
from PyQt5 import QtWidgets,  QtGui
from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLineEdit, QHBoxLayout)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent
from PyQt5.uic import loadUi
import logging
import settings
from settings import Settings
import ImageLabel
import json
import threading
from datetime import datetime

from  serialstatus import FDProtocol
import serial
from xmlrpc.client import ServerProxy
import xmlrpc.client

import subprocess
import numpy as np

import myconstdef

files = []

#CURSOR_NEW = QtGui.QCursor(QtGui.QPixmap('cursor.png'))

def listImages(path):
#path = 'c:\\projects\\hc2\\'
    # r=root, d=directories, f = files
    for r, _, f in os.walk(path):
        for file in f:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                files.append(os.path.join(r, file))

class DrawPicThread(QThread):
    #signal = pyqtSignal('PyQt_PyObject')
    def __init__(self, imagelabel, index):
        QThread.__init__(self)
        self.imagelabel=imagelabel
        self.index = index

    def run(self):
        import testrsync
        logging.info(datetime.now().strftime("%H:%M:%S.%f")+"   call rsync++")
        #process = subprocess.Popen(["rsync", "-avzP", '--delete', '/tmp/ramdisk', "pi@192.168.1.16:/tmp/ramdisk"],
        #    stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        #process.stdin.write(b'qa\n')
        #process.communicate()[0]
        #process.wait()
        testrsync.rsync()
        logging.info(datetime.now().strftime("%H:%M:%S.%f")+"   call rsync--")
        #process.stdin.close()
        self.imagelabel.imagepixmap = QPixmap("/tmp/ramdisk/phoneimage_%d.jpg" % self.index)#pixmap

        #status = self.imagelabel.DrawImageResults(self.data)
        #self.signal.emit((self.index, status))


class StatusCheckThread(QThread):
#https://kushaldas.in/posts/pyqt5-thread-example.html
    signal = pyqtSignal(int)
    def __init__(self):
        QThread.__init__(self)
        self.serialport = "/dev/ttyUSB0"
        self.exit_event = threading.Event()

    # run method gets called when we start the thread
    def run(self):
        ser = serial.serial_for_url('alt://{}'.format(self.serialport), baudrate=9600, timeout=1)
    #ser = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=1)
        status=-1
        oldstatus=-1
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
                    if status != 3:
                        status = 3
                if oldstatus!=status:
                    self.signal.emit(status)
                    oldstatus = status
                #time.sleep(0.05)
                self.msleep(50)

class UISettings(QDialog):
    """Settings dialog widget
    """
    #filepath=""
    pixmap = None
    keyboardID=0
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
        #self.resized.connect(self.someFunction)
        self.pbSetting.clicked.connect(self.on_settingclick)
        self.pbKeyBoard.clicked.connect(self.on_KeyBoardclick)
        self.checkBox.stateChanged.connect(self.btnstate)
        self.tabWidget.currentChanged.connect(self.on_CameraChange)
        self.comboBox.currentTextChanged.connect(self.OnChangeItem)
        self.leProfile.hide()
        self.previewEvent = threading.Event()
        self.imageTop.SetCamera(ImageLabel.CAMERA.TOP)
        self.imageLeft.SetCamera(ImageLabel.CAMERA.LEFT)
        self.imageRight.SetCamera(ImageLabel.CAMERA.RIGHT)
        self.takelock=threading.Lock()
        self.takepic=threading.Event()
        self.startKey =False
        self.client = ServerProxy(myconstdef.URL, allow_none=True)
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

        #self.serialThread = StatusCheckThread()
        #self.serialThread.signal.connect(self.StatusChange)
 
        self.threadPreview=None
        #self.imageResults=[0]*3
        self.profileimages=["","",""]

    def StatusChange(self, value):
        self.takelock.acquire()
        print("value is :"+str(value))
        if (value == 2):
            self.OnPreview()
        elif(value == 1):
            self.previewEvent.set() 
            time.sleep(0.1)
            #start process
            #self.on_startclick()
        self.takelock.release()

    #@staticmethod
    def createKeyboard(self):
        #subprocess.Popen(["killall","matchbox-keyboa"])
        #self.keyboardID = 0
        if self.keyboardID == 0:
            p = subprocess.Popen(["matchbox-keyboard", "--xid"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.keyboardID = int(p.stdout.readline())
            threading.Thread(target=lambda : print(p.stdout.readline())).start()
            self.startKey = True
            logging.debug("capturing window 0x%x ", self.keyboardID)
            embed_window = QtGui.QWindow.fromWinId(self.keyboardID)
            embed_widget = QtWidgets.QWidget.createWindowContainer(embed_window)
            embed_widget.setMinimumWidth(580)
            embed_widget.setMinimumHeight(280)
            hbox2 = QHBoxLayout()
            hbox2.addWidget(embed_widget)
            self.wdtKeyBoard.setLayout(hbox2)



    def ShowKeyBoard(self):
        try:
            if self.startKey:
                self.wdtKeyBoard.hide()
                self.startKey = False
                return

            self.createKeyboard()
            if self.keyboardID == 0:
                return
            self.wdtKeyBoard.show()
            self.startKey = True
            #elf.wdtKeyBoard.resize(580, 280)
        except:
            pass


    def OnChangeItem(self, value):
        index = self.comboBox.currentIndex()
        if(index>=0):
            self.config['comboxindex'] = index
        self._saveConfigFile()
        
        self.profileimages[0]=os.path.join(self.config["profilepath"], self.comboBox.currentText(), "top", self.comboBox.currentText()+".jpg")
        self.profileimages[1]=os.path.join(self.config["profilepath"], self.comboBox.currentText(), "left", self.comboBox.currentText()+".jpg")
        self.profileimages[2]=os.path.join(self.config["profilepath"], self.comboBox.currentText(), "right", self.comboBox.currentText()+".jpg")


    def _saveConfigFile(self):
        with open('config.json', 'w') as json_file:
            json.dump(self.config, json_file, indent=4)

    def createprofiledirstruct(self, profiename):
        if os.path.isfile('config.json'):
            with open('config.json') as json_file:
                self.config = json.load(json_file)

        self.client = ServerProxy(myconstdef.URL, allow_none=True)

    def closeEvent(self, event):
        self.previewEvent.set()
        while self.threadPreview.is_alive():
            time.sleep(0.1)
        self._shutdown()
        self.serialThread.exit_event.set()
        self.close()


    def resizeEvent(self, event):
        self.resized.emit()
        return super(UISettings, self).resizeEvent(event)

    '''def someFunction(self):
        logging.info(str(self.width())+"X"+str(self.height()))   '''

    def changeStyle(self, styleName):
        QApplication.setStyle(QStyleFactory.create(styleName))
        QApplication.setPalette(QApplication.style().standardPalette())

    def updateProfile(self):
        self.createprofiledirstruct("")
        fpath=self.config["profilepath"]
        #client = ServerProxy("http://localhost:8888", allow_none=True)
        self.comboBox.addItems(self.client.updateProfile(fpath))
        self.comboBox.setCurrentIndex(self.config["comboxindex"] if 'comboxindex' in self.config else 0)
        #curpath=os.path.abspath(os.path.dirname(sys.argv[0]))
        #profilepath=os.path.join(curpath,"profiles")
        #self.comboBox.addItems([name for name in os.listdir(profilepath) if os.path.isdir(os.path.join(profilepath, name))])

    @staticmethod
    def createSShServer():
        from paramiko import SSHClient
        import paramiko
        ssh = SSHClient()
        #ssh.set_missing_host_key_policy(AutoAddPolicy())
        ssh.load_system_host_keys()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=myconstdef.IP, username='pi', password=myconstdef.PASSWORD, look_for_keys=False)

        stdin, stdout, stderr = ssh.exec_command('DISPLAY=:0.0 python3 ~/Desktop/pyUI/servertask.py')
        bErrOut = True
        
        for line in stdout.read().splitlines():
            bErrOut = False
            break

        if bErrOut:
            for line in stderr.read().splitlines():
                print(line)
                break
        
        ssh.close()


    '''    
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
    '''

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
            cmd='rsync -avz -e ssh pi@%s:/home/pi/Desktop/pyUI/profiles/  /home/pi/Desktop/pyUI/profiles/' % myconstdef.IP
            os.system(cmd)
            self.comboBox.show()
    '''
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
    '''

    @pyqtSlot()
    def on_CameraChange(self):
        return


    @pyqtSlot()
    def on_KeyBoardclick(self):
        self.ShowKeyBoard()

    @pyqtSlot()
    def on_settingclick(self):
        dlg = Settings(self)
        if dlg.exec_():
            print("Success!")
        else:
            print("Cancel!")  

        #self.ShowKeyBoard()      

    @pyqtSlot()
    def on_click(self):
        sender = self.sender()
        clickevent = sender.text()
        if clickevent == u'Image UP':
            self.previewEvent.set() 
            time.sleep(0.1)
            self.client.startpause(True)
        else:
            self.OnPreview()
    
    def _loadprofileimages(self):
        if not self.checkBox.isChecked():
            profilename= self.leProfile.text() if self.checkBox.isChecked() else self.comboBox.currentText()
            #self.client.profilepath(self.config["profilepath"], profilename)
            pathleft = os.path.join(self.config["profilepath"], profilename, "left")
            pathtop = os.path.join(self.config["profilepath"], profilename, "top")
            pathright = os.path.join(self.config["profilepath"], profilename, "right")
            self.profileimages[0]=os.path.join(pathtop,  profilename+".jpg")
            self.profileimages[1]=os.path.join(pathleft,  profilename+".jpg")
            self.profileimages[2]=os.path.join(pathright,  profilename+".jpg")
            self.imageTop.setImageScale()
            self.imageTop.imagepixmap = QPixmap(self.profileimages[0])
            self.imageLeft.setImageScale()
            self.imageLeft.imagepixmap = QPixmap(self.profileimages[1])
            self.imageRight.setImageScale()
            self.imageRight.imagepixmap = QPixmap(self.profileimages[2])



    def _showImage(self, index, imagelabel):
        print(datetime.now().strftime("%H:%M:%S.%f"),"Start testing %d" % index)
        self.client.TakePicture(index, not self.checkBox.isChecked())   
        print(datetime.now().strftime("%H:%M:%S.%f"),"Start transfer %d" % index)
        imagelabel.setImageScale()     
        if self.checkBox.isChecked():
            data = self.client.imageDownload(index).data
            print(datetime.now().strftime("%H:%M:%S.%f"),"end testing %d" % index)
            image = Image.open(io.BytesIO(data))
            image.save("/tmp/ramdisk/temp_%d.jpg" % index)
            #imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
            #pixmap = QPixmap.fromImage(imageq)
            imagelabel.imagepixmap = QPixmap("/tmp/ramdisk/temp_%d.jpg" % index)#pixmap
        else:
            '''data = self.client.imageDownload(index).data
            print(datetime.now().strftime("%H:%M:%S.%f"),"end testing %d" % index)
            image = Image.open(io.BytesIO(data))
            image.save("/tmp/ramdisk/temp_%d.jpg" % index)
            #imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
            #pixmap = QPixmap.fromImage(imageq)'''
            #imagelabel.imagepixmap = QPixmap("/tmp/ramdisk/temp_%d.jpg" % index)#pixmap
            if not os.path.exists(self.profileimages[index]):
                logging.info("profile image file not found."+self.profileimages[index])
            #imagelabel.imagepixmap = QPixmap(self.profileimages[index])#"/tmp/ramdisk/temp_%d.jpg" % index)
            imagelabel.SetProfile(self.leProfile.text(), self.leProfile.text()+".jpg")
        #self.picthread = DrawPicThread(imagelabel, index)
        #self.picthread.start()

    def _drawtestScrew(self, index, imagelabel):
        ret=0
        ret = imagelabel.DrawImageResults(json.loads(self.client.ResultTest(index)))
        return ret

    def _ThreadTakepicture(self):
        profilename= self.leProfile.text() if self.checkBox.isChecked() else self.comboBox.currentText()
        self.client.profilepath(self.config["profilepath"], profilename)
        pathleft = os.path.join(self.config["profilepath"], profilename, "left")
        pathtop = os.path.join(self.config["profilepath"], profilename, "top")
        pathright = os.path.join(self.config["profilepath"], profilename, "right")
        self.profileimages[0]=os.path.join(pathtop,  profilename+".jpg")
        self.profileimages[1]=os.path.join(pathleft,  profilename+".jpg")
        self.profileimages[2]=os.path.join(pathright,  profilename+".jpg")

        self.takelock.acquire()
        status, status1, status2 = 0, 0, 0
        self.takepic.clear()
        try:
            self._showImage(0, self.imageTop)
            self._showImage(1, self.imageLeft)
            self._showImage(2, self.imageRight)
        except Exception as ex:
            print(str(ex))
            status = 5
        finally:
            self.takelock.release()

        print(datetime.now().strftime("%H:%M:%S.%f"),"ending camera and transfer")
        self.takepic.set()

    @pyqtSlot()
    def on_startclick(self):
        if self.leProfile.text()=="" and self.checkBox.isChecked():
            error_dialog = QtWidgets.QErrorMessage(self)
            error_dialog.showMessage('Oh no! Profile name is empty.') 
            return             
        
        print(datetime.now().strftime("%H:%M:%S.%f"),"Start testing click")
        self.previewEvent.set() 
        while self.threadPreview.is_alive():
            time.sleep(0.1)

        '''
        self.client.profilepath(self.config["profilepath"], self.leProfile.text() if self.checkBox.isChecked() else self.comboBox.currentText())
        print(datetime.now().strftime("%H:%M:%S.%f"),"Start testing %d" % 0)
        self.client.TakePicture(0, self.checkBox.isChecked())   
        print(datetime.now().strftime("%H:%M:%S.%f"),"Start transfer %d" % 0)
        self.imageTop.setImageScale()     
        data = self.client.imageDownload(0).data
        print(datetime.now().strftime("%H:%M:%S.%f"),"end testing %d" % 0)
        image = Image.open(io.BytesIO(data))
        image.save("/tmp/ramdisk/aaa.jpg")
        #imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
        #pixmap = QPixmap.fromImage(imageq)
        #self.imageTop.setServerProxy(self.client)
        self.imageTop.imagepixmap = QPixmap("/tmp/ramdisk/aaa.jpg")#pixmap
        self.imageTop.SetProfile(self.leProfile.text(), self.leProfile.text()+".jpg")
        '''
        p = threading.Thread(target=self._ThreadTakepicture)
        p.start()
        #Process(target=self._loadprofileimages).start()
        if not self.checkBox.isChecked():
            status, status1, status2 = 0, 0, 0
            self.takepic.wait()
            self.takepic.clear()
            #time.sleep(1)
            try:
                print(datetime.now().strftime("%H:%M:%S.%f"),"Start Draw Info")
                #status=self._drawtestScrew(0, self.imageTop, json.loads(self.client.ResultTest(0)))  
                data = json.loads(self.client.ResultTest(0))
                data=[]
                if len(data)>0:  
                    status = self.imageTop.DrawImageResults(data, QPixmap(self.profileimages[0]) )
                #status1=self._drawtestScrew(1, self.imageLeft, json.loads(self.client.ResultTest(1)))
                data = json.loads(self.client.ResultTest(1))
                data=[]
                if len(data)>0:
                    status1 = self.imageLeft.DrawImageResults(data, QPixmap(self.profileimages[1]))
                #status2=self._drawtestScrew(2, self.imageRight, json.loads(self.client.ResultTest(2)))
                data = json.loads(self.client.ResultTest(2))
                data=[]
                if len(data)>0:
                    status2 = self.imageRight.DrawImageResults(data, QPixmap(self.profileimages[2]))
                print(datetime.now().strftime("%H:%M:%S.%f"),"End Draw Info")
            except :
                status = 5

            status = max([status, status1, status2])
            if status==0:
                self.lblStatus.setText("success")
                self.lblStatus.setStyleSheet('''
                color: green
                ''')
            elif status==1:
                self.lblStatus.setText("finish")
                self.lblStatus.setStyleSheet('''
                color: yellow
                ''')
            else:
                self.lblStatus.setText("Error")
                self.lblStatus.setStyleSheet('''
                color: red
                ''')

        print(datetime.now().strftime("%H:%M:%S.%f"),"task finished")

        return

    def _shutdown(self):
        #client = ServerProxy("http://localhost:8888", allow_none=True)
        try:
            self.client.CloseServer()
        except :
            pass


    def _GetImageShow(self):
        self.imageTop.setImageScale() 
        logging.info(self.client.startpause(False))
        time.sleep(0.1)
        while True:
            data = self.client.preview().data
            image = Image.open(io.BytesIO(data))
            imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
            pixmap = QPixmap.fromImage(imageq)
            #self.imageTop.imagepixmap = pixmap
            self.imageTop.ShowPreImage(pixmap)
            if self.previewEvent.is_set():
                self.previewEvent.clear()
                self.client.startpause(True)
                break

    def ChangeTab(self):
        time.sleep(0.1)
        window.tabWidget.setCurrentIndex(0)
        time.sleep(0.1)
        window.tabWidget.setCurrentIndex(1)
        time.sleep(0.1)
        window.tabWidget.setCurrentIndex(2)
        time.sleep(0.1)
        window.tabWidget.setCurrentIndex(0)
        #self.serialThread.start()


    def OnPreview(self):
        #self.client.startpause(False)
        if self.threadPreview==None or not self.threadPreview.is_alive():
            self.threadPreview= threading.Thread(target=self._GetImageShow)
            self.threadPreview.start()
        
 
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)   
    app = QApplication(sys.argv)
    window = UISettings()
    
    window.show()
    window.showFullScreen()

    threading.Thread(target=window.ChangeTab).start()

    logging.info(str(window.width())+"X"+str(window.height()))   
    sys.exit(app.exec_())
