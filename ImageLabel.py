from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal,QPoint, QRect
from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLabel)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent
import logging
import profiledata
import os
import sys
import enum
from datetime import datetime
from xmlrpc.client import ServerProxy
import numpy as np
import myconstdef
import resource


class CAMERA(enum.Enum):
   TOP = 0
   LEFT = 1
   RIGHT = 2

class ImageLabel(QLabel):
    #LEFTCAMERA, TOPCAMERA, RIGHTCAMERA=range(3)
    def __init__(self, parent=None):
        super(ImageLabel, self).__init__(parent)
        self.logger = logging.getLogger('PSILOG')
        self.setMouseTracking(True)
        self.CURSOR_NEW = QCursor(QPixmap(':/icons/cursor.png').scaled(25,25, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.CUR_CUESOR = self.cursor()
        self._imagepixmap = None
        self._imagepixmapback = None
        self.w = 0
        self.h = 0
        self.scalex =0.0
        self.scaley =0.0
        self.imagel = 0
        self.imaget = 0
        #self.screwW = myconstdef.screwWidth
        #self.screwH = myconstdef.screwHeight
        self._isProfile = False
        self.ProfilePoint=[]
        self._camerapoisition=CAMERA.TOP
        self.profile=profiledata.profile("","")
        self._indexscrew=0
        self.profilerootpath=os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])),"profiles")
        self._client = ServerProxy(myconstdef.URL, allow_none=True)
        self.imagedresult=0


    def fileprechar(self, argument):
        switcher = {
            CAMERA.LEFT: "L",
            CAMERA.TOP: "T",
            CAMERA.RIGHT: "R",
        }
        return switcher.get(argument, "Invalid")

    def setServerProxy(self, value):
        self._client = value

    # get profile directory sub directory
    def DirSub(self, argument):
        switcher = {
            CAMERA.LEFT: "left",
            CAMERA.TOP: "top",
            CAMERA.RIGHT: "right",
        }
        return switcher.get(argument, "Invalid")

    def SetProfile(self, profilename, filename):
        self.profile.profilename = profilename
        self.profile.filename = filename

    def SetCamera(self, which):
        self._camerapoisition = which

    def setImageScale(self):
        if self.w == 0 or self.h ==0:
            self.w = self.width()
            self.h = self.height()
            self.logger.info("uilabel:"+str(self.w)+"X"+str(self.h))

    @property
    def isProfile(self):
        return self._isProfile

    @isProfile.setter
    def isProfile(self, value):
        self._isProfile = value

    @property
    def imagepixmap(self):
        return self._imagepixmap

    @imagepixmap.setter
    def imagepixmap(self, value):
        self._imagepixmap = value
        self._imagepixmapback = value.copy()
        self.setPixmap(value.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.scalex = float(value.width()) / self.pixmap().width()
        self.scaley = float(value.height()) / self.pixmap().height()
        self.imagel = (self.width() - self.pixmap().width())/2
        self.imaget = (self.height() - self.pixmap().height())/2
        self.logger.info("lblimage:"+str(self.pixmap().width())+"X"+str(self.pixmap().height()))
        self.logger.info(self.scalex)
        self.logger.info(self.scaley)


    def mouseInImage(self, x, y):
        if self._imagepixmap == None:
            return False
        if x>=self.imagel and x <= self.imagel+self.pixmap().width() and y>=self.imaget and y <= self.imaget+self.pixmap().height():
            return True
        
        return False

    def _savescrew(self, pt):
        screwLeft = int(myconstdef.screwWidth /2)
        screwRight = int(myconstdef.screwWidth - screwLeft)
        screwTop = int(myconstdef.screwHeight / 2)
        screwBottom = int(myconstdef.screwHeight - screwTop)
        x = pt.x()-screwLeft if pt.x()-screwLeft > 0 else 0
        y = pt.y()-screwTop if pt.y()-screwTop > 0 else 0

        #x = pt.x()-self.screwW if pt.x()-self.screwW > 0 else 0
        #y = pt.y()-self.screwH if pt.y()-self.screwH > 0 else 0
        #x1 = pt.x() + self.screwW if pt.x() + self.screwW < self._imagepixmapback.width() else self._imagepixmapback.width()
        #y1 = pt.y() + self.screwH if pt.y() + self.screwH < self._imagepixmapback.height() else self._imagepixmapback.height()
 
        x1 = pt.x() + screwRight if pt.x() + screwRight < self._imagepixmapback.width() else self._imagepixmapback.width()
        y1 = pt.y() + screwBottom if pt.y() + screwBottom < self._imagepixmapback.height() else self._imagepixmapback.height()
        
        currentQRect = QRect(QPoint(x,y),QPoint(x1 - 1, y1 - 1))
        cropQPixmap = self._imagepixmapback.copy(currentQRect)
        profilepath=os.path.join(self.profilerootpath, self.profile.profilename)
        filename = self.fileprechar(self._camerapoisition)+str(self._indexscrew)+".png" 
        profilepath=os.path.join(profilepath, self.DirSub(self._camerapoisition), filename)
        cropQPixmap.save(profilepath)
        screwpoint = profiledata.screw(self.profile.profilename, filename, pt, QPoint(x,y), QPoint(x1,y1))
        self.ProfilePoint.append(screwpoint)
        sinfo = profilepath+", "+str(x)+", "+str(x1)+", "+str(y)+", "+str(y1)
        profiletxt = os.path.join(self.profilerootpath, self.profile.profilename, self.DirSub(self._camerapoisition),  self.profile.profilename+".txt")
        self.append_new_line(profiletxt, sinfo)
        self._indexscrew+=1



    def append_new_line(self, file_name, text_to_append):
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

    def ShowPreImage(self, image):
        self._imagepixmap = image
        self.setPixmap(self._imagepixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))    


    def DrawImageResults(self, data, imagepic):
        self.logger.info("DrawImageResults ++ " + str(self._camerapoisition))
        ret=0
        self.imagedresult = ret
        if imagepic is not None:
            self._imagepixmap = imagepic
        if self._imagepixmap == None or len(data)==0:
            self.imagedresult = ret
            return ret
        self.logger.info(data)
        painterInstance = QPainter(self._imagepixmap)
        penRectangle = QPen(Qt.red)
        penRectangle.setWidth(12)

        for itemscrew in data:
            location = itemscrew[1]
            if itemscrew[0] == np.nan or itemscrew[0] < 0.35:
                ret = 2
                penRectangle.setColor(Qt.red)
            elif itemscrew[0] >= 0.45:
                penRectangle.setColor(Qt.green)
            else:
                if ret != 2:
                    ret= 1 
                penRectangle.setColor(Qt.yellow)

            painterInstance.setPen(penRectangle)
            painterInstance.drawRect(QRect(QPoint(location[0], location[2]),QPoint(location[1], location[3])))

        self.setPixmap(self._imagepixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))    
        painterInstance.end()
        self.imagedresult = ret
        logging.info("DrawImageResults -- ")
        return ret

    def DrawImageProfile(self, data, imagepic):
        self.logger.info("DrawImageProfile ++ " + str(self._camerapoisition))
        ret=0
        if imagepic is not None:
            self._imagepixmap = imagepic
        if self._imagepixmap == None or len(data)==0:
            return ret
        self.logger.info(data)
        painterInstance = QPainter(self._imagepixmap)
        penRectangle = QPen(Qt.red)
        penRectangle.setWidth(6)
        painterInstance.setPen(penRectangle)

        for pt in data:
            # draw rectangle on painter
            painterInstance.drawEllipse(QPoint(pt[0],pt[1]),myconstdef.screwWidth,myconstdef.screwHeight)

        self.setPixmap(self._imagepixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))    
        painterInstance.end()
        self.imagedresult = ret
        logging.info("DrawImageProfile -- ")
        return ret


    def DrawImageResult(self, location, clr = Qt.red):
        if self._imagepixmap == None:
            return

        painterInstance = QPainter(self._imagepixmap)
        # set rectangle color and thickness
        penRectangle = QPen(clr)
        penRectangle.setWidth(3)

        # draw rectangle on painter
        painterInstance.setPen(penRectangle)
        #painterInstance.drawEllipse(QPoint(x * self.scalex, y*self.scaley),25,25)
        painterInstance.drawRect(QRect(QPoint(location[0], location[2]),QPoint(location[1], location[3])))
        #self.ProfilePoint.append(QPoint(x * self.scalex, y*self.scaley))

        # set pixmap onto the label widget
        self.setPixmap(self._imagepixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))    
        painterInstance.end()


    def DrawImage(self, x, y, clr = Qt.red):
        # convert image file into pixmap
        #pixmap = QPixmap(self.filepath)
        self.logger.info("draw:"+str(x)+"=>"+str(y)) 
        if self._imagepixmap == None or not self._isProfile:
            return
        # create painter instance with pixmap

        realx = int (x * self.scalex)
        realy = int (y * self.scaley)
        self.logger.info("draw real point:"+str(x)+"=>"+str(y)) 
        self.logger.info("source image:"+str(self._imagepixmap.width())+"=>"+str(self._imagepixmap.height())) 
        try:
            painterInstance = QPainter(self._imagepixmap)

            # set rectangle color and thickness
            penRectangle = QPen(clr)
            penRectangle.setWidth(6)

            # draw rectangle on painter
            painterInstance.setPen(penRectangle)
            painterInstance.drawEllipse(QPoint(realx, realy),myconstdef.screwWidth,myconstdef.screwHeight)
            painterInstance.drawText(QPoint(realx+myconstdef.screwWidth, realy+myconstdef.screwHeight), str(self._indexscrew))
            #self.ProfilePoint.append(QPoint(x * self.scalex, y*self.scaley))

            # set pixmap onto the label widget
            self.setPixmap(self._imagepixmap.scaled(self.w,self.h, Qt.KeepAspectRatio, Qt.SmoothTransformation))    
            painterInstance.end()
        except Exception as ex:
            self.logger.info(str(ex))
            pass

        #self._client.CreateSamplePoint(self._camerapoisition.value, x * self.scalex, y*self.scaley)
        if self._client == None:
            self._savescrew(QPoint(realx, realy))
        else:
            self._client.CreateSamplePoint(self._camerapoisition.value, realx, realy)

    def mousePressEvent(self, evt):
        self.logger.info("mousepress:"+str(evt.pos().x())+"=>"+str(evt.pos().y())) 
        if self.mouseInImage(evt.pos().x(), evt.pos().y()):
            self.DrawImage(evt.pos().x()-self.imagel, evt.pos().y()-self.imaget)


    def enterEvent(self, event):
        QApplication.setOverrideCursor(self.CURSOR_NEW)

    def leaveEvent(self, event):
        QApplication.setOverrideCursor(self.CUR_CUESOR)
