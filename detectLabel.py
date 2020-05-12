from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal,QPoint, QRect
from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLabel)
from PyQt5.QtGui import QPixmap, QImage, QPainter,QPen
import logging

import os
import sys

from datetime import datetime
import PhotoViewer

class DetectLabel(QLabel):
    #LEFTCAMERA, TOPCAMERA, RIGHTCAMERA=range(3)
    def __init__(self, parent=None):
        super(DetectLabel, self).__init__(parent)
        self.logger = logging.getLogger('PSILOG')
        self._imagepixmap = None
        self.imagedresult=0
        self._camerapoisition = PhotoViewer.CAMERA.TOP
        self.profilepoints = []
        self.profilerootpath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"profiles")

    @property
    def imagepixmap(self):
        return self._imagepixmap

    @imagepixmap.setter
    def imagepixmap(self, value):
        self._imagepixmap = value
        self.setPixmap(value.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def SetCamera(self, which):
        self._camerapoisition = which


    def ShowPreImage(self, image):
        self._imagepixmap = image
        self.setPixmap(self._imagepixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))    


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
        penRectangle.setWidth(3)

        for itemscrew in data:
            location = itemscrew[1]
            if itemscrew[0] < 0.35:
                ret = 2
                penRectangle.setColor(Qt.red)
            elif itemscrew[0] >= 0.45:
                penRectangle.setColor(Qt.green)
            else:
                if ret != 2:
                    ret= 1 
                penRectangle.setColor(Qt.yellow)

            painterInstance.setPen(penRectangle)
            painterInstance.drawRect(QRect(QPoint(int(location[0]/4), int(location[2]/4)),QPoint(int(location[1]/4), int(location[3]/4))))

        painterInstance.end()
        self.setPixmap(self._imagepixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))    
        self.imagedresult = ret
        self.logger.info("DrawImageResults -- " + str(self._camerapoisition))
        return ret

    # get profile directory sub directory
    def DirSub(self, argument):
        switcher = {
            PhotoViewer.CAMERA.LEFT: "left",
            PhotoViewer.CAMERA.TOP: "top",
            PhotoViewer.CAMERA.RIGHT: "right",
        }
        return switcher.get(argument, "Invalid")


    def DrawProfile(self, profilename):
        self.logger.info("DrawImageProfile ++ " + str(self._camerapoisition))
        ret=0
        imagename=os.path.join(self.profilerootpath, profilename, self.DirSub(self._camerapoisition), profilename+".jpg")
        txtname=os.path.join(self.profilerootpath, profilename, self.DirSub(self._camerapoisition), profilename+".txt")
        if not os.path.exists(imagename):
            self.logger.info(imagename)
            return 1
        self.LoadProfilePoints(txtname)
        _imagepixmap = QPixmap(imagename)
        painterInstance = QPainter(_imagepixmap)
        penRectangle = QPen(Qt.red)
        penRectangle.setWidth(3)
        painterInstance.setPen(penRectangle)

        for pt in self.profilepoints:
            # draw rectangle on painter
            painterInstance.drawEllipse(pt.centrpoint, pt.rect.width() / 2, pt.rect.height() / 2)

        self.ShowPreImage(self._imagepixmap)
        painterInstance.end()
        self.logger.info("DrawImageProfile -- " + str(self._camerapoisition))
        return ret

    def LoadProfilePoints(self, fname):
        if fname == None or fname == '':
            fname=os.path.join(self.profilerootpath, self.DirSub(index), self.profile.profilename+".txt")

        if os.path.exists(fname):
            self.profilepoints = []
            with open(fname) as f:
                for line in f:
                    words = line.split()                    
                    roi_0 = int(words[1][:-1])
                    roi_1 = int(words[2][:-1])
                    roi_2 = int(words[3][:-1])
                    roi_3 = int(words[4])
                    self.profilepoints.append(PhotoViewer.ProfilePoint(roi_0,roi_2, roi_1, roi_3))
                    #x = roi_0 + int((roi_1 - roi_0 + 1)/2)
                    #y = roi_2 + int((roi_3 - roi_2 + 1)/2)
                    #centerpoint.append((x,y))

            return True
        
        return False
