#!/usr/bin/python3
def lockFile(lockfile):
    import fcntl
    fp = open(lockfile, 'w')
    try:
        fcntl.lockf(fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except IOError:
        return False
    return True

if not lockFile(".lock.pid"):
    sys.exit(0)

import sys
import os
import io
import time
#import picamera
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal
from PyQt5 import QtWidgets,  QtGui
from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLineEdit, QHBoxLayout, QMessageBox)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent,QKeySequence
from PyQt5.uic import loadUi
import logging
from login import LoginDialog
import PhotoViewer
import json
import threading
from multiprocessing import Process
from datetime import datetime
import shutil
import cv2

from  serialstatus import FDProtocol
import serial
from xmlrpc.client import ServerProxy
import xmlrpc.client

import subprocess
import numpy as np

import testScrew
import myconstdef
import resource
from CSICamera import CSI_Camera
import dlgResult

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
        self.logger.info(datetime.now().strftime("%H:%M:%S.%f")+"   call rsync++")
        #process = subprocess.Popen(["rsync", "-avzP", '--delete', '/tmp/ramdisk', "pi@192.168.1.16:/tmp/ramdisk"],
        #    stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        #process.stdin.write(b'qa\n')
        #process.communicate()[0]
        #process.wait()
        testrsync.rsync()
        self.logger.info(datetime.now().strftime("%H:%M:%S.%f")+"   call rsync--")
        #process.stdin.close()
        self.imagelabel.imagepixmap = QPixmap("/tmp/ramdisk/phoneimage_%d.jpg" % self.index)#pixmap

        #status = self.imagelabel.DrawImageResults(self.data)
        #self.signal.emit((self.index, status))


class StatusCheckThread(QThread):
#https://kushaldas.in/posts/pyqt5-thread-example.html
    signal = pyqtSignal(int)
    def __init__(self, myvar, parent=None):
        QThread.__init__(self, parent)        
        self.serialport = "/dev/ttyUSB0"
        self.exit_event = threading.Event()
        self.mylock = myvar
        self.threhold = 40000
        #sudo usermod -a -G tty qa
        #sudo chown qa /dev/ttyUSB0
        os.system("echo %s | sudo -S usermod -a -G tty qa" % myconstdef.PASSWORD)
        os.system("echo %s | sudo -S chown qa /dev/ttyUSB0" % myconstdef.PASSWORD)

    def setThrehold(self, value):
        self.threhold = value
    # run method gets called when we start the thread
    def run(self):
        ser = serial.serial_for_url('alt://{}'.format(self.serialport), baudrate=115200, timeout=1)
    #ser = serial.Serial('/dev/ttyUSB0', baudrate=9600, timeout=1)
        status=-1
        oldstatus=-1
        with serial.threaded.ReaderThread(ser, FDProtocol) as statusser:
            while not self.exit_event.is_set():
                statusser.setProxThreshold(self.threhold)
                if statusser.proximityStatus and statusser.laserStatus:
                    if status!=1:
                        status=1
                        #do task start
                elif not statusser.proximityStatus:
                    if status!=2:
                        status=2
                        #start preview
                elif not statusser.laserStatus:
                    if status != 3:
                        status = 3
                if not self.mylock.locked():
                    if oldstatus != status:
                        self.signal.emit(status)
                        oldstatus = status
                #time.sleep(0.05)
                self.msleep(50)
            statusser.stop()

class UISettings(QDialog):
    """Settings dialog widget
    """
    #filepath=""
    keyboardID=0
    #resized = pyqtSignal()
    imageview = pyqtSignal(QPixmap, int)
    ViewerPreViewMode = pyqtSignal(bool)
    ClearImageShow = pyqtSignal(int)
    ShowRepeatTime = pyqtSignal(int)
    def __init__(self, parent=None):
        super(UISettings, self).__init__()
        self.logger = logging.getLogger('PSILOG')
        spathUI = os.path.join(os.path.dirname(os.path.realpath(__file__)),"psi_auto.ui")
        loadUi(spathUI, self)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.changeStyle('Fusion')
        self.takelock = threading.Lock()
        self.takepic = threading.Event()
        self.stop_prv = threading.Event()
        self.stop_DryRun = threading.Event()

        self.pbClose.clicked.connect(self.closeEvent)
        self.tabImages.tabBar().hide()
        self.tabSetting.tabBar().hide()
        self.tabAllSetting.tabBar().hide()
        self.leUserID.setText("12345")
        self.pbTop.clicked.connect(self.on_CameraChange)
        self.pbLeft.clicked.connect(self.on_CameraChange)
        self.pbRight.clicked.connect(self.on_CameraChange)
        self.pbtabDryrun.clicked.connect(self.On_settingChange)
        self.pbtabSetting.clicked.connect(self.On_settingChange)
        self.pbtabProfile.clicked.connect(self.On_settingChange)
        self.pbExitSetting.clicked.connect(self.On_ExitSettingMode)

        self.pbStart.clicked.connect(self.on_startclick)
        self.pbFinish.clicked.connect(self.on_startPreview)
        self.pbShowSetting.clicked.connect(self.On_ShowSetting)
        self.pbSettingSave.clicked.connect(self.On_SaveSetting)
        self.pbDryRunStart.clicked.connect(self.On_DryRun)
        self.pbDryRunStop.clicked.connect(self.On_DryRun)

        self.clientA = CSI_Camera()
        self.clientB = CSI_Camera()
        self.pbProfileSelect.clicked.connect(self.On_ShowProfile)
        self.pbProfileEdit.clicked.connect(self.On_EditProfile)

        self.serialThread = StatusCheckThread(self.takelock)
        self.config=myconstdef.DEFAULTCONFIG
        self._loadConfigFile()
        self.updateProfile()
        self.imageview.connect(self._ShowpixmapGView)
        self.ViewerPreViewMode.connect(self.PreviewMode)
        self.ClearImageShow.connect(self._ClearImageShow)
        self.ShowRepeatTime.connect(self._ShowRepeatTime)
        #self.pbSetting.clicked.connect(self.on_settingclick)
        #self.pbKeyBoard.clicked.connect(self.on_KeyBoardclick)
        self.cbAutoStart.stateChanged.connect(self.btnstate)

        #self.leIMEI.setInputMask('9')
        self.leDeviceID.editingFinished.connect(self.on_imei_editfinished)
        self.leModel.editingFinished.connect(self.on_model_editfinished)
        #self.leProfile.hide()
        #self.previewEvent = threading.Event()

        self.imageTop.SetCamera(PhotoViewer.CAMERA.TOP)
        self.imageLeft.SetCamera(PhotoViewer.CAMERA.LEFT)
        self.imageRight.SetCamera(PhotoViewer.CAMERA.RIGHT)

        self.startKey =False
        self.clientleft = ServerProxy(myconstdef.URL_LEFT, allow_none=True)
        #self.clienttop = ServerProxy(myconstdef.URL_TOP, allow_none=True)
        #self.clientright = ServerProxy(myconstdef.URL_RIGHT, allow_none=True)
        self.setStyleSheet('''
        QPushButton{background-color:rgb(68, 114, 196);
            color: white;   
            border-radius: 5px;}
		QPushButton:hover{background-color:white; 
            color: black;}
		QPushButton:pressed{background-color:rgb(85, 170, 255);}
        QWidget#Dialog{
            background:gray;
            border-top:1px solid white;
            border-bottom:1px solid white;
            border-left:1px solid white;
            border-top-left-radius:10px;
            border-bottom-left-radius:10px;
        }''')

        self.serialThread.signal.connect(self.StatusChange)
        self.pbAddProfile.clicked.connect(self.On_AddProfile)
        self.pbDoneProfile.clicked.connect(self.On_DoneProfile)
        self.pbProfileSave.clicked.connect(self.On_SaveProfile)
        self.pbProfileNew.clicked.connect(self.On_ProfileNew)
        self.leProfileStationID.returnPressed.connect(self.On_ProfileTakePic)
        self.leProfileModel.returnPressed.connect(self.On_ProfileTakePic)
        #self.listWidget.itemDoubleClicked.connect(self.On_ListWidgetDoubleClick)

        ######Add ShortCut Begin######### 
        self.scAdd = QtWidgets.QShortcut(QKeySequence("Ctrl+A"), self)
        self.scAdd.activated.connect(self.On_AddProfile)
        
        self.scSave = QtWidgets.QShortcut(QKeySequence("Ctrl+S"), self)
        self.scSave.activated.connect(self.On_SaveSetting)

        self.scNew = QtWidgets.QShortcut(QKeySequence("Ctrl+N"), self)
        self.scNew.activated.connect(self.On_ProfileNew)

        self.scResult = QtWidgets.QShortcut(QKeySequence("Ctrl+R"), self)
        self.scResult.activated.connect(self.On_ShowDryRunResult)

        self.scDelProfile = QtWidgets.QShortcut(QKeySequence("Ctrl+D"), self)
        self.scDelProfile.activated.connect(self.On_DeleteProfile)
        ######Add ShortCut End########### 
        self.threadPreview = None
        self.threadDryrun = None
        #self.imageResults=[0]*3
        self.profileimages = ["", "", ""]
        self.imageresults = []
        self.yanthread = None
        self._profilepath = ""  #with profile name
        self.profilename = ""
        self.isProfilestatus = False

        self.imeidb = None
        self.loadImeidb()
        self.serialThread.start()
        self.dryrunResult = []
        self.ProfileImages =[]
        self.previewpixEvent = threading.Event()

    def PreviewMode(self, v):
        self.imageTop.toggleReviewMode(v)
        self.imageLeft.toggleReviewMode(v)
        self.imageRight.toggleReviewMode(v)

    def _ShowpixmapGView(self, pixmap, v):
        self.logger.info("_ShowpixmapGView ++")
        if v == PhotoViewer.CAMERA.TOP.value:
            if self.previewpixEvent.is_set():
                if pixmap.height()==720:
                    self.previewpixEvent.clear()
                    return
            self.imageTop.ShowPreImage(pixmap)
        elif v == PhotoViewer.CAMERA.LEFT.value:
            self.imageLeft.ShowPreImage(pixmap)
        elif v == PhotoViewer.CAMERA.RIGHT.value:
            self.imageRight.ShowPreImage(pixmap)
        self.logger.info("_ShowpixmapGView --")

    def loadImeidb(self):
        if os.path.isfile('imei2model.json'):
            with open('imei2model.json') as json_file:
                self.imeidb = json.load(json_file)

    def ImeiQuery(self, imei):
        #"cmc_maker": "Apple",
        #"cmc_model": "iPhone3GS",
        #"maker": "Apple",
        #"model": "iPhone3GS",
        if 'doc' in self.imeidb:
            for item in self.imeidb['doc']:
                if imei.startswith(item['uuid']):
                    maker = item['maker'] if 'maker' in item else ''
                    model = item['model'] if 'model' in item else ''
                    cmc_maker = item['cmc_maker'] if 'cmc_maker' in item else ''
                    cmc_model = item['cmc_model'] if 'cmc_model' in item else ''
                    return (maker, model, cmc_maker, cmc_model)
        return ('', '', '', '')

    def _getProfileName(self):
        self.profilename = ''
        if self.leModel.text() !="" and self.lblStationID.text() != '':
            self.profilename = self.leModel.text() +'_'+self.lblStationID.text()
            self.config["phonemodel"] = self.leModel.text()
            self._saveConfigFile()
            return True
        return False

    def on_imei_editfinished(self):
        if len(self.leIMEI.text())>=8:
            _,model,_,_ = self.ImeiQuery(self.leIMEI.text())
            self.leModel.setText(model)
            self._getProfileName()

    def on_model_editfinished(self):
        self._getProfileName()        

    def StatusChange(self, value):
        self.takelock.acquire()
        print("value is :"+str(value))
        if (value == 3):
            self.lblStatus.setText("ready")
            self.lblStatus.setStyleSheet('''
            color: black
            ''')
        elif (value == 2):
            if self.isAutoDetect or self.isProfilestatus:
                self.OnPreview()
        elif(value == 1):
            #self.previewEvent.set() 
            #start process
            self._stopPreview()
            if self.isAutoDetect:
                self.on_startclick()
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
            self.logger.debug("capturing window 0x%x ", self.keyboardID)
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


    def _saveConfigFile(self):
        try:
            with open('config.json', 'w') as json_file:
                json.dump(self.config, json_file, indent=4)
        except Exception as e:
            print(e)
            self.logger.exception(str(e))


    def _loadConfigFile(self):
        if os.path.isfile('config.json'):
            with open('config.json') as json_file:
                self.config = json.load(json_file)

        myconstdef.screwWidth = self.config['screww'] if 'screww' in self.config else 40
        myconstdef.screwHeight = self.config['screwh']  if 'screwh' in self.config else 40
        self.isPreview = self.config['preview'] if 'preview' in self.config else True
        self.isAutoDetect = self.config["autostart"] if 'autostart' in self.config else True
        self.cbAutoStart.setChecked(self.isAutoDetect)
        spath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"profiles")
        self.sProfilePath = self.config["profilepath"] if 'profilepath' in self.config else spath
        self.lblStationID.setText(self.config["stationid"] if 'stationid' in self.config else '1')
        self.leStationID.setText(self.lblStationID.text())
        self.leModel.setText(self.config["phonemodel"] if 'phonemodel' in self.config else '')
        self.serialThread.setThrehold(self.config["threhold"] 
                                      if 'threhold' in self.config else 20000)


    def createprofiledirstruct(self, profiename):
        self.clientA.startCamera(0)
        self.clientB.startCamera(1)
        self.clientleft = ServerProxy(myconstdef.URL_LEFT, allow_none=True)
        #self.clienttop = ServerProxy(myconstdef.URL_TOP, allow_none=True)
        #self.clientright = ServerProxy(myconstdef.URL_RIGHT, allow_none=True)
        self.imageLeft.setServerProxy(self.clientleft)
        #self.imageTop.setServerProxy(self.clienttop)
        #self.imageRight.setServerProxy(self.clientright)

    def closeEvent(self, event):
        self._stopPreview()
        self._saveConfigFile()
        self._shutdown()
        self.serialThread.exit_event.set()
        self.close()

    def changeStyle(self, styleName):
        QApplication.setStyle(QStyleFactory.create(styleName))
        QApplication.setPalette(QApplication.style().standardPalette())

    def updateProfile(self):
        self.createprofiledirstruct("")

    def _GetImageShow(self):
        self.logger.info("preview: thread starting...")
        
        #if self.isProfilestatus:
            #return
        self.imageTop.setImageScale()
        self.imageTop.toggleReviewMode(True)
        self.stop_prv.clear()
        while True:
            _ , data=self.clientA.read()
            img = cv2.cvtColor(data, cv2.COLOR_BGR2RGB)
            image = Image.fromarray(img)
            imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
            pixmap = QPixmap.fromImage(imageq)
            #self.imageTop.ShowPreImage(pixmap)
            self.imageview.emit(pixmap, PhotoViewer.CAMERA.TOP.value)
            if self.stop_prv.is_set():
                self.stop_prv.clear()
                break

        self.stop_prv.clear()
        if self.isProfilestatus:
            self.previewpixEvent.set()
        self.logger.info("preview: thread ending...")


    @pyqtSlot()
    def btnstate(self):
        if self.sender().isChecked():
            self.pbStart.setEnabled(False)
            self.pbFinish.setEnabled(False)
            self.isAutoDetect = True
            self.config["autostart"] = True
        else:
            self.pbStart.setEnabled(True)
            self.pbFinish.setEnabled(True)
            self.isAutoDetect = False
            self.config["autostart"] = False

    @pyqtSlot()
    def On_ExitSettingMode(self):
        self.tabSetting.setCurrentIndex(0)
        self.tabAllSetting.setCurrentIndex(0)
        #self.imageTop.fitInView()
        self.imageTop.toggleReviewMode(True)
        #self.imageLeft.fitInView()
        self.imageLeft.toggleReviewMode(True)
        #self.imageRight.fitInView()
        self.imageRight.toggleReviewMode(True)
        self.isAutoDetect = self.config["autostart"]
        self.isProfilestatus = False
        if not self.isAutoDetect:
            self.pbStart.setEnabled(True)
            self.pbFinish.setEnabled(True)



    @pyqtSlot()
    def On_ShowSetting(self):
        dlg = LoginDialog(self)
        if not dlg.exec_():
            return 
        self.isAutoDetect = False
        self.tabSetting.setCurrentIndex(1)
        self.pbtabDryrun.setStyleSheet('''background-color:  rgb(255, 255, 255);color: rgb(0, 0, 0);''')
        self.pbtabSetting.setStyleSheet('''background-color:  rgb(255, 255, 255);color: rgb(0, 255, 0);''')
        self.pbtabProfile.setStyleSheet('''background-color:  rgb(255, 255, 255);color: rgb(0, 0, 0);''')
        self.leStationID.setText(self.config["stationid"] if 'stationid' in self.config else '1')
        self.isProfilestatus = True
        self._saveConfigFile()

    
    @pyqtSlot()
    def On_SaveSetting(self):
        self.config['stationid'] = self.leStationID.text()
        self._saveConfigFile()
        self.lblStationID.setText(self.leStationID.text())

    @pyqtSlot()
    def On_DryRun(self):
        sender = self.sender()
        clickevent = sender.text()
        if clickevent == u'Start':
            if self.threadDryrun==None or not self.threadDryrun.is_alive():
                self.threadDryrun= threading.Thread(target=self.__jason)
                self.threadDryrun.start()            
        elif clickevent == u'Stop':
            self.stop_DryRun.set()

    @pyqtSlot()
    def On_ListWidgetDoubleClick(self, item):
        proname = item.text()
        pathleft = os.path.join(self.sProfilePath, proname, "left")
        pathtop = os.path.join(self.sProfilePath, proname, "top")
        pathright = os.path.join(self.sProfilePath, proname, "right")
            
        self.profileimages[PhotoViewer.CAMERA.TOP.value]=os.path.join(pathtop,  proname+".jpg")
        self.profileimages[PhotoViewer.CAMERA.LEFT.value]=os.path.join(pathleft,  proname+".jpg")
        self.profileimages[PhotoViewer.CAMERA.RIGHT.value]=os.path.join(pathright,  proname+".jpg")

        self._stopPreview()
            
        self.profilename = proname
        self._loadProfile()
        bbb = proname.split('_' )
        self.leModel.setText('_'.join(bbb[:-1]))
        self.config['stationid'] = bbb[-1]
        self.lblStationID.setText(bbb[-1])
        self._saveConfigFile()
        self.On_ExitSettingMode()

    def _stopPreview(self):
        if self.threadPreview is not None and self.threadPreview.is_alive():
            self.stop_prv.set() 
            while self.threadPreview is not None and self.threadPreview.is_alive():
                time.sleep(0.1)

    @pyqtSlot()
    def On_EditProfile(self):
        curIndex = self.listWidget.currentRow()
        if curIndex < 0:
            QMessageBox.question(self, 'Error', "Oh no! Select Profile please.", QMessageBox.No, QMessageBox.No)
            return             
        proname = self.listWidget.currentItem().text()
        
        self._stopPreview()

        

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            pathleft = os.path.join(self.sProfilePath, proname, "left")
            pathtop = os.path.join(self.sProfilePath, proname, "top")
            pathright = os.path.join(self.sProfilePath, proname, "right")
                
            self.profileimages[PhotoViewer.CAMERA.TOP.value]=os.path.join(pathtop,  proname+".jpg")
            self.profileimages[PhotoViewer.CAMERA.LEFT.value]=os.path.join(pathleft,  proname+".jpg")
            self.profileimages[PhotoViewer.CAMERA.RIGHT.value]=os.path.join(pathright,  proname+".jpg")
            
            self.profilename = proname
            self._loadProfile()
            #do edit
        finally:
            QApplication.restoreOverrideCursor() 

    @pyqtSlot()
    def On_DeleteProfile(self):
        if self.listWidget.currentRow()>=0:     
            proname = self.listWidget.currentItem().text()
            self.logger.info("delete:"+proname)            
            #self.clienttop.RemoveProfile(proname)
            #self.clientright.RemoveProfile(proname)
            dirPath=os.path.join(self.data["profilepath"], proname)
            try:
                shutil.rmtree(dirPath)
            except Exception as e:
                print(e)
                self.logger.exception(str(e))
                self.logger.error('Error while deleting directory')
            self.listWidget.takeItem(self.listWidget.currentRow())


    @pyqtSlot()
    def On_ShowProfile(self):
        curIndex = self.listWidget.currentRow()
        if curIndex < 0:
            QMessageBox.question(self, 'Error', "Oh no! Select Profile please.", QMessageBox.No, QMessageBox.No)
            return             
        proname = self.listWidget.currentItem().text()
        
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            pathleft = os.path.join(self.sProfilePath, proname, "left")
            pathtop = os.path.join(self.sProfilePath, proname, "top")
            pathright = os.path.join(self.sProfilePath, proname, "right")
                
            self.profileimages[PhotoViewer.CAMERA.TOP.value]=os.path.join(pathtop,  proname+".jpg")
            self.profileimages[PhotoViewer.CAMERA.LEFT.value]=os.path.join(pathleft,  proname+".jpg")
            self.profileimages[PhotoViewer.CAMERA.RIGHT.value]=os.path.join(pathright,  proname+".jpg")

            self._stopPreview()
                
            self.profilename = proname
            self.isProfilestatus = False
            self._loadProfile()
            bbb = proname.split('_' )
            self.leModel.setText('_'.join(bbb[:-1]))
            self.config['stationid'] = bbb[-1]
            self.lblStationID.setText(bbb[-1])
            self._saveConfigFile()
            self.On_ExitSettingMode()
        finally:
            QApplication.restoreOverrideCursor() 


    @pyqtSlot()
    def On_settingChange(self):
        if self.threadDryrun is not None and self.threadDryrun.is_alive():
            return

        self.pbtabDryrun.setStyleSheet('''background-color:  rgb(255, 255, 255);color: rgb(0, 0, 0);''')
        self.pbtabSetting.setStyleSheet('''background-color:  rgb(255, 255, 255);color: rgb(0, 0, 0);''')
        self.pbtabProfile.setStyleSheet('''background-color:  rgb(255, 255, 255);color: rgb(0, 0, 0);''')

        sender = self.sender()
        clickevent = sender.text()
        if clickevent == u'Setting':
            self.tabAllSetting.setCurrentIndex(0)
            self.pbtabSetting.setStyleSheet('''background-color:  rgb(255, 255, 255);color: rgb(0, 255, 0);''')
        elif clickevent == u'Profile':
            self.tabAllSetting.setCurrentIndex(1)
            self.listWidget.clear()
            self.pbtabProfile.setStyleSheet('''background-color:  rgb(255, 255, 255);color: rgb(0, 255, 0);''')
            
            self.listWidget.addItems([name for name in os.listdir(self.sProfilePath) if os.path.isdir(os.path.join(self.sProfilePath, name))])
            #for name in os.listdir(self.sProfilePath):
            #    if os.path.isdir(os.path.join(self.sProfilePath, name)):
            #        self.listWidget.addItem(name)
        else:
            self.pbtabDryrun.setStyleSheet('''background-color:  rgb(255, 255, 255);color: rgb(0, 255, 0);''')
            self.tabAllSetting.setCurrentIndex(2)
            self.sbRepeatTime.setValue(self.config['repeattime']  if 'repeattime' in self.config else 100)



    @pyqtSlot()
    def on_CameraChange(self):
        sender = self.sender()
        clickevent = sender.text()
        if clickevent == u'TOP':
            self.tabImages.setCurrentIndex(0)
        elif clickevent == u'LEFT':
            self.tabImages.setCurrentIndex(1)
        else:
            self.tabImages.setCurrentIndex(2)



    @pyqtSlot()
    def on_KeyBoardclick(self):
        self.ShowKeyBoard()

    def __jason(self):
        self.isAutoDetect = False
        self.config['repeattime'] = self.sbRepeatTime.value()
        self.stop_DryRun.clear()
        irepeat = self.sbRepeatTime.value()
        self.isProfilestatus = False
        self.dryrunResult = []
        while not self.stop_DryRun.is_set() and irepeat>0:
            self.logger.info("auto dry run Left %d" % irepeat)
            self.on_startclick()
            irepeat -= 1
            #self.sbRepeatTime.setValue(irepeat)
            self.ShowRepeatTime.emit(irepeat)
            time.sleep(2)
        self.isProfilestatus = True

    @pyqtSlot()
    def on_startPreview(self):
        if not self.isProfilestatus:
            self.OnPreview()
    
    def _DirSub(self, argument):
        switcher = {
            1: "left",
            0: "top",
            2: "right",
        }
        return switcher.get(argument, "Invalid")

    def runsyncprofiles(self, isLeft):
        ip = myconstdef.IP_LEFT        
        cmd = 'rsync -avz -e ssh pi@{0}:{1}/ {2}/'.format(ip, '/home/pi/Desktop/pyUI/profiles',self.config["profilepath"])
        os.system(cmd)

    def capture(self, cam, IsDetect=True):
        #cmd = "raspistill -vf -hf -ISO 50 -n -t 50 -o /tmp/ramdisk/phoneimage_%d.jpg" % cam
        #if cam ==0:
        #    cmd = "raspistill -ISO 50 -n -t 50 -o /tmp/ramdisk/phoneimage_%d.jpg" % cam
        #logging.info(cmd)
        #os.system(cmd)
        client = self.clientA if cam==0 else self.clientB
        _ , data=client.read()
        img = cv2.cvtColor(data, cv2.COLOR_BGR2RGB)
        image = Image.fromarray(img)
        image.save("/tmp/ramdisk/phoneimage_%d.jpg" % cam)
        if not IsDetect:
            shutil.copyfile("/tmp/ramdisk/phoneimage_%d.jpg" % cam, os.path.join(self._profilepath, self._DirSub(cam), self.profilename+".jpg"))
        else:
            self._callyanfunction(cam)

    def _callyanfunction(self, index):
        #self.profilename= self.leProfile.text() if self.checkBox.isChecked() else self.comboBox.currentText()
        self.logger.info('callyanfunction:' + self.profilename)
        txtfilename=os.path.join(self._profilepath, self._DirSub(index), self.profilename+".txt")
        smplfilename=os.path.join(self._profilepath, self._DirSub(index), self.profilename+".jpg")
        self.logger.info(txtfilename)
        self.logger.info(smplfilename)
        if os.path.exists(txtfilename) and os.path.exists(smplfilename):
            self.logger.info("*testScrews**")
            try:
                self.imageresults = testScrew.testScrews(
                    txtfilename, 
                    smplfilename, 
                    "/tmp/ramdisk/phoneimage_%d.jpg" % index)
            except :
                self.imageresults = []
                pass
            
            self.logger.info("-testScrews end--")
            self.logger.info(self.imageresults)

    def _startdetectthread(self, index):
        self.yanthread = Process(target=self._callyanfunction, args=(index,))
        self.yanthread.start()
        self.yanthread.join()

    def _showImage(self, index, imagelabel):
        imagelabel.setImageScale()     
        self.logger.info("Start testing %d" % index)
        if index==ImageLabel.CAMERA.LEFT.value:
            self.clientleft.TakePicture(index, not self.checkBox.isChecked()) 
        else: 
            self.capture(index, not self.checkBox.isChecked())

        self.logger.info("Start transfer %d" % index)
        imagelabel.SetProfile(self.profilename, self.profilename+".jpg")
        if self.isProfilestatus:
            if index!=PhotoViewer.CAMERA.LEFT.value:
                self.imageview.emit(QPixmap("/tmp/ramdisk/phoneimage_%d.jpg" % index), index)
                #imagelabel.ShowPreImage(QPixmap("/tmp/ramdisk/phoneimage_%d.jpg" % index))#pixmap
            else:
                #data = self.clientleft.imageDownload(index).data if index == 1 else self.clientright.imageDownload(index).data
                data = self.clientleft.imageDownload(index).data
                self.logger.info("end testing %d" % index)
                image = Image.open(io.BytesIO(data))
                image.save("/tmp/ramdisk/temp_%d.jpg" % index)
                #imageq = ImageQt(image) #convert PIL image to a PIL.ImageQt object
                #pixmap = QPixmap.fromImage(imageq)
                #imagelabel.ShowPreImage(QPixmap("/tmp/ramdisk/temp_%d.jpg" % index))#pixmap
                self.imageview.emit(QPixmap("/tmp/ramdisk/temp_%d.jpg" % index), index)
                #self.imageview.emit(pixmap)
        else:
            #imagelabel.SetProfile(self.profilename, self.profilename+".jpg")
            if index==PhotoViewer.CAMERA.LEFT.value:
                pass

    def _drawtestScrew(self, index, imagelabel):
        ret=0
        if index!=PhotoViewer.CAMERA.LEFT.value:
            ret = imagelabel.DrawImageResults(self.imageresults)
        else:
            ss = self.clientleft.ResultTest(index)
            #ss = self.clienttop.ResultTest(index) if index==1 else self.clientright.ResultTest(index)
            ret = imagelabel.DrawImageResults(json.loads(ss))
        return ret

    def _ThreadTakepictureLeft(self):
        try:
            self._showImage(PhotoViewer.CAMERA.LEFT.value, self.imageLeft)
        except Exception as ex:
            self.logger.exception(str(ex))
            status = 5

        self.logger.info("ending camera Left and transfer")

    def _ThreadTakepictureRight(self):
        try:
            self._showImage(PhotoViewer.CAMERA.RIGHT.value, self.imageRight)
        except Exception as ex:
            self.logger.exception(str(ex))
            status = 5

        self.logger.info("ending camera right and transfer")


    def _ThreadTakepicture(self):
        self.takepic.clear()
        try:
            self._showImage(PhotoViewer.CAMERA.TOP.value, self.imageTop)
        except Exception as ex:
            self.logger.exception(str(ex))
            status = 5

        self.logger.info("ending camera A and transfer")

    def DrawResultTop(self):
        #self.lblImageTop.clear()
        self.ClearImageShow.emit(0x1)
        self.imageTop.imagedresult = 0
		self.imageLeft.DrawImageResults(self.imageresults, self.ProfileImages[PhotoViewer.CAMERA.TOP.value].copy(self.ProfileImages[PhotoViewer.CAMERA.TOP.value].rect()))

        #data = json.loads(self.clienttop.ResultTest(PhotoViewer.CAMERA.TOP.value))
        #if len(data)>0:
        #    status1 = self.imageTop.DrawImageResults(data, self.ProfileImages[PhotoViewer.CAMERA.TOP.value].copy(self.ProfileImages[PhotoViewer.CAMERA.TOP.value].rect()))

    def DrawResultLeft(self):
        #self.lblImageLeft.clear()
        self.ClearImageShow.emit(0x2)
        self.imageLeft.imagedresult = 0
        self.imageLeft.DrawImageResults(self.imageresults, self.ProfileImages[PhotoViewer.CAMERA.LEFT.value].copy(self.ProfileImages[PhotoViewer.CAMERA.LEFT.value].rect()))

    def DrawResultRight(self):
        #self.lblImageRight.clear()
        self.ClearImageShow.emit(0x4)
        self.imageRight.imagedresult = 0
		self.imageRight.DrawImageResults(self.imageresults, self.ProfileImages[PhotoViewer.CAMERA.RIGHT.value].copy(self.ProfileImages[PhotoViewer.CAMERA.RIGHT.value].rect()))
        #data = json.loads(self.clientright.ResultTest(PhotoViewer.CAMERA.RIGHT.value))
        #if len(data)>0:
        #    status2 = self.imageRight.DrawImageResults(data, self.ProfileImages[PhotoViewer.CAMERA.RIGHT.value].copy(self.ProfileImages[PhotoViewer.CAMERA.RIGHT.value].rect()))

    def _loadProfile(self):
        self.imageTop.DrawProfile(self.profilename)
        self.imageLeft.DrawProfile(self.profilename)
        self.imageRight.DrawProfile(self.profilename)

    def _ClearImageShow(self, index):
        if index & 0x1 == 0x1:
            self.imageTop.clear()
        if index & 0x2 == 0x2:
            self.imageLeft.clear()
        if index & 0x4 == 0x4:
            self.imageRight.clear()

    def _ShowRepeatTime(self, repeat):
        self.sbRepeatTime.setValue(repeat)

    @pyqtSlot()
    def On_ShowDryRunResult(self):
        dlg = dlgResult.ResultDialog(self.dryrunResult, self)
        dlg.exec_()

    @pyqtSlot()
    def on_startclick(self):
        if self.isProfilestatus:
            return

        self._getProfileName()
        if self.profilename=="":
            QMessageBox.question(self, 'Error', "Oh no! Profile name is empty.", QMessageBox.Cancel, QMessageBox.Cancel)
            return             
        
        #self.ClearImageShow.emit(0xf)

        pathleft = os.path.join(self.sProfilePath, self.profilename, "left")
        pathtop = os.path.join(self.sProfilePath, self.profilename, "top")
        pathright = os.path.join(self.sProfilePath, self.profilename, "right")
            
        self.profileimages[PhotoViewer.CAMERA.TOP.value]=os.path.join(pathtop,  self.profilename+".jpg")
        self.profileimages[PhotoViewer.CAMERA.LEFT.value]=os.path.join(pathleft,  self.profilename+".jpg")
        self.profileimages[PhotoViewer.CAMERA.RIGHT.value]=os.path.join(pathright,  self.profilename+".jpg")

        if len(self.ProfileImages) == 0:
            self.ProfileImages.append(QPixmap(self.profileimages[PhotoViewer.CAMERA.TOP.value]).scaledToHeight(820))
            self.ProfileImages.append(QPixmap(self.profileimages[PhotoViewer.CAMERA.LEFT.value]).scaledToHeight(820))
            self.ProfileImages.append(QPixmap(self.profileimages[PhotoViewer.CAMERA.RIGHT.value]).scaledToHeight(820))
            self.ProfileImages.append(self.profilename)
        elif self.ProfileImages[3]!=self.profilename:
            self.ProfileImages[PhotoViewer.CAMERA.TOP.value]= QPixmap(self.profileimages[PhotoViewer.CAMERA.TOP.value]).scaledToHeight(820)
            self.ProfileImages[PhotoViewer.CAMERA.LEFT.value]= QPixmap(self.profileimages[PhotoViewer.CAMERA.LEFT.value]).scaledToHeight(820)
            self.ProfileImages[PhotoViewer.CAMERA.RIGHT.value]= QPixmap(self.profileimages[PhotoViewer.CAMERA.RIGHT.value]).scaledToHeight(820)
            self.ProfileImages[3] = self.profilename


        self._stopPreview()

        self._profilepath = os.path.join(self.sProfilePath, self.profilename)
        if not self.isProfilestatus and not os.path.exists(self._profilepath):
            QMessageBox.question(self, 'Error', "Oh no! Create profile please.", QMessageBox.Cancel, QMessageBox.Cancel)
            return  

        if self.startKey:
            self.ShowKeyBoard()

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            try:
                self.clientleft.profilepath(self.sProfilePath, self.profilename)        
            except:
                pass
            
            #try:
            #    self.clienttop.profilepath(self.sProfilePath, self.profilename)
            #except:
            #    pass

            self.logger.info("Start testing click")
            self.logger.info("Start testing top")
            p = threading.Thread(target=self._ThreadTakepicture)
            p.start()
            pLeft = threading.Thread(target=self._ThreadTakepictureLeft)
            pLeft.start()
            pRight = threading.Thread(target=self._ThreadTakepictureRight)
            pRight.start()
            p.join()
            self.logger.info("Start end top")        
            pLeft.join()
            self.logger.info("Start end left")        
            pRight.join()
            self.logger.info("Start end right")        
            #if not self.isProfilestatus:
            status, status1, status2 = 0, 0, 0
            #self.takepic.wait()
            #self.takepic.clear()
            try:
                self.logger.info("Start Draw Thread Info")
                
                #threads=[]
                ttop = threading.Thread(target=self.DrawResultTop)
                ttop.start()
                #threads.append(ttop)
                
                tleft = threading.Thread(target=self.DrawResultLeft)
                tleft.start()
                #threads.append(tleft)

                tright = threading.Thread(target=self.DrawResultRight)
                tright.start()
                #threads.append(tright)
                self.logger.info("Draw Thread started")

                ttop.join()
                self.logger.info("Draw top finish")
                tleft.join()
                self.logger.info("Draw left finish")
                tright.join()
                self.logger.info("Draw right finish")
                #for t in threads:
                #    t.join()
                
                status = self.imageTop.imagedresult
                status1 = self.imageLeft.imagedresult
                status2 = self.imageRight.imagedresult
                self.logger.info("End Draw Info:%d:%d:%d"%(status, status1, status2))
            except :
                status = 5

            self.dryrunResult.append([status, status1, status2])
            status = max([status, status1, status2])
            if status==0:
                self.lblStatus.setText("")
                self.lblStatus.setStyleSheet('''
                border-image: url(:/icons/yes.png); 
                ''')
            elif status==1:
                self.lblStatus.setText("")
                self.lblStatus.setStyleSheet('''
                border-image: url(:/icons/warning.png);
                ''')
            else:
                self.lblStatus.setText("")
                self.lblStatus.setStyleSheet('''
                border-image: url(:/icons/no.png); 
                ''')

            self.logger.info("task finished")

        except Exception as e:
            self.logger.exception(str(e))
        finally:
            QApplication.restoreOverrideCursor() 



    def _shutdown(self):
        try:
            #self.clienttop.CloseServer()
            #self.clientright.CloseServer()
			self.clientleft.CloseServer()
        except :
            pass

    def ChangeTab(self):
        time.sleep(0.1)
        window.tabImages.setCurrentIndex(0)
        time.sleep(0.1)
        window.tabImages.setCurrentIndex(1)
        time.sleep(0.1)
        window.tabImages.setCurrentIndex(2)
        time.sleep(0.1)
        self.logger.info(str(self.lblStatus.width())+"X"+str(self.lblStatus.height()))
        self.lblStatus.setFixedSize(self.lblStatus.width(),self.lblStatus.width())
        self.logger.info("Status Size:"+str(self.lblStatus.width())+"X"+str(self.lblStatus.height()))
        window.tabImages.setCurrentIndex(0)
        self.serialThread.start()
        self.imageTop.setImageScale() 
        self.imageLeft.setImageScale() 
        self.imageRight.setImageScale() 


    def OnPreview(self):
        allowpreview = self.config["preview"] if 'preview' in self.config else True
        if not allowpreview:
            return
        if self.threadPreview==None or not self.threadPreview.is_alive():
            self.threadPreview= threading.Thread(target=self._GetImageShow)#self.PreviewCamera)
            self.threadPreview.start()

    def On_DoneProfile(self):
        if self.imageTop.needSaveProfile() or self.imageLeft.needSaveProfile() or self.imageRight.needSaveProfile():
            reply = QMessageBox.question(self, 'Info', "Do you want to save Profile?", QMessageBox.Cancel | QMessageBox.Yes, QMessageBox.Cancel)
            if reply == QMessageBox.Yes:
                self.On_SaveProfile()
        self.tabAllSetting.setCurrentIndex(1)

    def On_AddProfile(self):
        if self.tabImages.currentIndex() == PhotoViewer.CAMERA.TOP.value:
            self.imageTop.AddProfilePoint()
        elif self.tabImages.currentIndex() == PhotoViewer.CAMERA.LEFT.value:
            self.imageLeft.AddProfilePoint()
        elif self.tabImages.currentIndex() == PhotoViewer.CAMERA.RIGHT.value:
            self.imageRight.AddProfilePoint()
    
    def On_SaveProfile(self):
        self.logger.info("On_SaveProfile ++ ")
        self.imageTop.SaveProfile()
        self.imageLeft.SaveProfile()
        self.imageRight.SaveProfile()
        items = self.listWidget.findItems(self.profilename, Qt.MatchExactly)
        if len(items) == 0:
            self.listWidget.addItem(self.profilename)
        self.logger.info("On_SaveProfile -- ")
        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            tl = Process(target=self.runsyncprofiles, args=(True,))
            tl.start()
            tr = Process(target=self.runsyncprofiles, args=(False,))
            tr.start()
            tl.join()
            tr.join()

        except Exception as e:
            self.logger.exception(str(e))
        finally:
            QApplication.restoreOverrideCursor() 

    def On_ProfileNew(self):
        if self.tabAllSetting.currentIndex() != 1:
            return
        self.tabAllSetting.setCurrentIndex(3)
        self.leProfileModel.setText('')
        self.leProfileStationID.setText('')
        self.imageTop.InitProfile()
        self.imageLeft.InitProfile()
        self.imageRight.InitProfile()
        try:
            #self.clienttop.cleanprofileparam()
            #self.clientright.cleanprofileparam()
			self.clientleft.cleanprofileparam()
        except Exception as e:
            self.logger.exception(str(e))


    def On_ProfileTakePic(self):
        if self.leProfileModel.text()=='' or self.leProfileStationID.text() == '':
            QMessageBox.question(self, 'Error', "Oh no! Profile name is empty.", QMessageBox.No, QMessageBox.No)
            return             
        
        profilename = self.leProfileModel.text() + "_" + self.leProfileStationID.text()
        self.profilename = profilename
        _profilepath = os.path.join(self.sProfilePath, profilename)
        if  os.path.exists(_profilepath):
            try:
                reply = QMessageBox.question(self, 'Error', "Profile exist. continue?", QMessageBox.No | QMessageBox.Yes, QMessageBox.No)
                if reply == QMessageBox.No:
                    return 
            except Exception as e:
                self.logger.exception(str(e)) 

        self.isProfilestatus = True
        
        pathleft = os.path.join(self.sProfilePath, profilename, "left")
        pathtop = os.path.join(self.sProfilePath, profilename, "top")
        pathright = os.path.join(self.sProfilePath, profilename, "right")
            
        self.profileimages[PhotoViewer.CAMERA.TOP.value]=os.path.join(pathtop,  profilename+".jpg")
        self.profileimages[PhotoViewer.CAMERA.LEFT.value]=os.path.join(pathleft,  profilename+".jpg")
        self.profileimages[PhotoViewer.CAMERA.RIGHT.value]=os.path.join(pathright,  profilename+".jpg")

        self._stopPreview()  

        self._profilepath = os.path.join(self.sProfilePath, profilename)

        mode = 0o777
        os.makedirs(pathleft, mode, True) 
        os.makedirs(pathtop, mode, True) 
        os.makedirs(pathright, mode, True) 
        
        if self.startKey:
            self.ShowKeyBoard()

        QApplication.setOverrideCursor(Qt.WaitCursor)
        try:
            try:
                self.clientleft.profilepath(self.sProfilePath, profilename)        
            except:
                pass
            
            #try:
            #    self.clienttop.profilepath(self.sProfilePath, profilename)
            #except:
            #    pass

            self.imageTop.isPreviewMode = False
            self.imageLeft.isPreviewMode = False
            self.imageRight.isPreviewMode = False
            self.logger.info("Start profile testing click")
            p = threading.Thread(target=self._ThreadTakepicture)
            p.start()
            pLeft = threading.Thread(target=self._ThreadTakepictureLeft)
            pLeft.start()
            pRight = threading.Thread(target=self._ThreadTakepictureRight)
            pRight.start()
            p.join()
            self.logger.info("Start profile end top")        
            pLeft.join()
            self.logger.info("Start profile end left")        
            pRight.join()
            self.logger.info("Start profile end right")  
            self.ViewerPreViewMode.emit(False)
        except Exception as e:
            self.logger.exception(str(e))
        finally:
            QApplication.restoreOverrideCursor() 


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

if __name__ == "__main__":
    if not lockFile(".lock.pid"):
        sys.exit(0)
    #%(threadName)s       %(thread)d
    #logging.basicConfig(stream=sys.stdout, level=logging.INFO, format='%(asctime)s - %(name)s[%(thread)d] - %(levelname)s - %(message)s')
    logger = CreateLog()
    app = QApplication(sys.argv)
    QApplication.processEvents()
    window = UISettings()
    
    window.show()
    window.showFullScreen()

    threading.Thread(target=window.ChangeTab).start()
    logger.info(os.path.dirname(os.path.realpath(__file__)))
    logger.info(str(window.width())+"X"+str(window.height()))   
    sys.exit(app.exec_())
