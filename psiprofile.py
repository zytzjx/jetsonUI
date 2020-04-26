#!/usr/bin/env python3
import sys
import os
import io
import time
import picamera
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLineEdit)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent
from PyQt5.uic import loadUi
import logging


files = []

#CURSOR_NEW = QtGui.QCursor(QtGui.QPixmap('cursor.png'))

def listImages(path):
#path = 'c:\\projects\\hc2\\'
    # r=root, d=directories, f = files
    for r, _, f in os.walk(path):
        for file in f:
            if file.lower().endswith(('.png', '.jpg', '.jpeg')):
                files.append(os.path.join(r, file))

class ImageCheckThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)
        self.git_url = ""

    # run method gets called when we start the thread
    def run(self):
        tmpdir = tempfile.mkdtemp()
        cmd = "git clone {0} {1}".format(self.git_url, tmpdir)
        subprocess.check_output(cmd.split())
        # git clone done, now inform the main thread with the output
        self.signal.emit(tmpdir)


class UISettings(QDialog):
    """Settings dialog widget
    """
    index = 0
    w = 0
    h = 0
    filepath=""
    pixmap = None
    def __init__(self, parent=None):
        super(UISettings, self).__init__()
        loadUi('PSI_profile.ui', self)
        self.changeStyle('Fusion')
        self.pbClose.clicked.connect(self.close)
        self.pbImageChange.clicked.connect(self.on_click)
        self.pbImageChangeDown.clicked.connect(self.on_click)
        self.pbStart.clicked.connect(self.on_startclick)
        self.updateProfile()

    #def mouseMoveEvent(self, evt: QMouseEvent) -> None:
    #    logging.info(str(evt.pos().x())+"=="+str(evt.pos().y())) 
    #    super(UISettings, self).mouseMoveEvent(evt)

    #def mousePressEvent(self, evt: QMouseEvent) -> None:
    #    logging.info(str(evt.pos().x())+"=>"+str(evt.pos().y())) 
    #    super(UISettings, self).mousePressEvent(evt)

    def changeStyle(self, styleName):
        QApplication.setStyle(QStyleFactory.create(styleName))
        QApplication.setPalette(QApplication.style().standardPalette())

    def updateProfile(self):
        self.comboBox.addItems(["main","left", "right"])
        self.comboBox.setCurrentIndex(0)
        self.comboBox.readonly=True
        self.comboBox.currentTextChanged.connect(self.on_combobox_changed)

    def on_combobox_changed(self, value):
        logging.info("combobox changed"+value)    
 
    def loadimage(self,filepath):
        pixmap = QPixmap(filepath)
        self.lblImage.setPixmap(pixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    
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
        self.lblImage.setPixmap(self.pixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))    
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
        #qimage = QImage(imageq) #cast PIL.ImageQt object to QImage object -that´s the trick!!!
        #pixmap = QPixmap(qimage)
        pixmap = QPixmap.fromImage(imageq)
        self.lblImage.imagepixmap = pixmap
        #self.lblImage.setPixmap(self.pixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))   



    @pyqtSlot()
    def on_click(self):
        sender = self.sender()
        clickevent = sender.text()
        if clickevent == u'Image UP':
            self.index+=1
            self.DrawImage(50,50)           
        else:
            self.index-=1
            self.PreviewCamera()

    @pyqtSlot()
    def on_startclick(self):
        if self.w ==0 or self.h ==0:
            #self.w = self.lblImage.width()
            #self.h = self.lblImage.height()
            self.lblImage.setImageScale()

        self.filepath = '/home/pi/Desktop/pyUI/curimage.jpg'
        with picamera.PiCamera() as camera:
            camera.start_preview()
            camera.capture(self.filepath)
            camera.stop_preview()   

        self.pixmap = QPixmap(self.filepath)
        logging.info(str(self.pixmap.width())+"X"+str(self.pixmap.height()))
        self.lblImage.imagepixmap = self.pixmap
        #self.lblImage.setPixmap(self.pixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation)) 
        #logging.info(str(self.lblImage.pixmap().width())+"X"+str(self.lblImage.pixmap().height()))
        #logging.info(str(self.w)+"X"+str(self.h))   


 
if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
    app = QApplication(sys.argv)
    #listImages('C:/Users/jefferyz/Desktop/pictures/')
    window = UISettings()
    #window.setModal(True)
    window.setWindowFlags(Qt.FramelessWindowHint)
    window.show()
    window.showFullScreen()
    
    #window.w = window.lblImage.width()
    #window.h = window.lblImage.height()
    #window.loadimage('C:/Users/jefferyz/Desktop/pictures/IMG_0001.PNG')
    
    logging.info(str(window.width())+"X"+str(window.height()))   
    sys.exit(app.exec_())
