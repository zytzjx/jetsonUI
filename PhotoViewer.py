from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent,QColor
from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal,QPoint, QRect
from PyQt5.QtWidgets import QGraphicsEllipseItem

import os
import logging
import enum
import profiledata
from xmlrpc.client import ServerProxy
import resource
import myconstdef


class CAMERA(enum.Enum):
   TOP = 0
   LEFT = 1
   RIGHT = 2

class ProfilePoint:
    def __init__(self, x1,y1,x2,y2):
        self.lefttop = QPoint(x1,y1)
        self.rightbottom = QPoint(x2,y2)
        self.centrpoint=QPoint(x1+int((x2-x1+1)/2), y1+int((y2-y1+1)/2))
        self.rect = QRect(x1,y1, x2-x1, y2-y1)
        self.screwDraw = 0
    
    def setCentrSize(self, pt, w, h):
        screwLeft = int(w /2)
        screwRight = int(w - screwLeft)
        screwTop = int(h / 2)
        screwBottom = int(h - screwTop)
        x = pt.x()-screwLeft if pt.x()-screwLeft > 0 else 0
        y = pt.y()-screwTop if pt.y()-screwTop > 0 else 0
        x1 = pt.x() + screwRight #if pt.x() + screwRight < self._imagepixmapback.width() else self._imagepixmapback.width()
        y1 = pt.y() + screwBottom #if pt.y() + screwBottom < self._imagepixmapback.height() else self._imagepixmapback.height()

        self.centrpoint = pt
        self.lefttop = QPoint(x,y)
        self.rightbottom = QPoint(x1,y1)
        self.rect = QRect(x,y,w,h)
        

class PhotoViewer(QtWidgets.QGraphicsView):
    photoClicked = QtCore.pyqtSignal(QtCore.QPoint)
    photoRightClicked = QtCore.pyqtSignal(QtCore.QPoint, QtCore.QPoint)
    showThreadImageUpdate = QtCore.pyqtSignal(QPixmap)
    MOUSEWIDTH = 100
    def __init__(self, parent):
        super(PhotoViewer, self).__init__(parent)
        self.logger = logging.getLogger('PSILOG')

        self._zoom = 0
        self._empty = True
        self._scene = QtWidgets.QGraphicsScene(self)
        self._photo = QtWidgets.QGraphicsPixmapItem()
        self._scene.addItem(self._photo)
        self.setScene(self._scene)
        self.setTransformationAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QtWidgets.QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        self.setBackgroundBrush(QtGui.QBrush(QtGui.QColor(11, 152, 60)))
        self.setFrameShape(QtWidgets.QFrame.NoFrame)

        self.photoRightClicked.connect(self.MouseRightClick)
        self.showThreadImageUpdate.connect(self.UpdateImage)

        self.CURSOR_NEW = QCursor(QPixmap(':/icons/cursor.png').scaled(PhotoViewer.MOUSEWIDTH, PhotoViewer.MOUSEWIDTH, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.CUR_CUESOR = self.cursor()
        self._imagepixmap = None
        #self._imagepixmapback = None
        self.w = 0
        self.h = 0
        self.imagedresult = 0
        self.isPreviewMode = True
        self.profilerootpath = os.path.join(os.path.dirname(os.path.realpath(__file__)),"profiles")
        self._camerapoisition = CAMERA.TOP
        self.profile = profiledata.profile("","")
        self.profilepoints = []
        self.pixRect = QRect()
        self.rightClickPoint = (QPoint(),QPoint())
        self.curfactor = 0.0
        self.screwDraw = 0
        self.screwReal= 0
        self._client = None

    def hasPhoto(self):
        return not self._empty

    def fitInSameImage(self):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                scenerect = self.transform().mapRect(rect)
                self.scale(1, 1)
            self._zoom = 10

    def fitInView(self, scale=True):
        rect = QtCore.QRectF(self._photo.pixmap().rect())
        if not rect.isNull():
            self.setSceneRect(rect)
            if self.hasPhoto():
                unity = self.transform().mapRect(QtCore.QRectF(0, 0, 1, 1))
                #print(str(unity.width())+"======"+str(unity.height()))
                self.scale(1 / unity.width(), 1 / unity.height())
                viewrect = self.viewport().rect()
                #print(viewrect)
                scenerect = self.transform().mapRect(rect)
                #print(scenerect)
                factor = min(viewrect.width() / scenerect.width(),
                             viewrect.height() / scenerect.height())
                #print(str(factor)+"======")
                self.scale(factor, factor)
                #scenerect = self.transform().mapRect(rect)
                #print(scenerect)
                self.curfactor = factor

            self._zoom = 0

    def checkPoint(self, pt):
        if self.pixRect != None and self.pixRect.isValid():
            return self.pixRect.contains(pt)
        return False


    def setPhoto(self, pixmap=None):
        self._zoom = 0
        if pixmap and not pixmap.isNull():
            self._empty = False
            if not self.isPreviewMode:
                self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self._photo.setPixmap(pixmap)
            self._imagepixmap = pixmap
            self.pixRect = self._photo.pixmap().rect()
        else:
            self._empty = True
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self._photo.setPixmap(QtGui.QPixmap())
            self._imagepixmap = QtGui.QPixmap()
            self.pixRect = QRect()
        self.fitInView()

    def wheelEvent(self, event):
        if self.isPreviewMode:
            return
        if self.hasPhoto():
            if event.angleDelta().y() > 0:
                factor = 1.1
                self._zoom += 1
            else:
                factor = 0.9
                self._zoom -= 1
            #print(str(factor)+"======"+str(self._zoom))
            if self._zoom > 0:
                if self._zoom == 10:
                    self.fitInSameImage()
                else:
                    self.scale(factor, factor)
            elif self._zoom == 0:
                self.fitInView()
            else:
                self._zoom = 0
            rect = QtCore.QRectF(self._photo.pixmap().rect())    
            scenerect = self.transform().mapRect(rect)
            self.curfactor = scenerect.width() / rect.width()
           


    def toggleReviewMode(self, yes):
        if yes:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
            self.isPreviewMode = True
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)
            self.isPreviewMode = False

    def toggleDragMode(self):
        if self.dragMode() == QtWidgets.QGraphicsView.ScrollHandDrag:
            self.setDragMode(QtWidgets.QGraphicsView.NoDrag)
        elif not self._photo.pixmap().isNull():
            self.setDragMode(QtWidgets.QGraphicsView.ScrollHandDrag)

    def mousePressEvent(self, event):
        #print("mousepress:"+str(event.pos().x())+"=>"+str(event.pos().y()))
        if self._photo.isUnderMouse():
            self.photoClicked.emit(self.mapToScene(event.pos()).toPoint())
        if event.button() == Qt.RightButton:
            self.photoRightClicked.emit(self.mapToScene(event.pos()).toPoint(), event.pos())
        super(PhotoViewer, self).mousePressEvent(event)

    def MouseRightClick(self, pt, pos):
        if self.checkPoint(pt):
            print("rightclick:"+str(pt.x())+"=>"+str(pt.y()))
            self.rightClickPoint = (pt, pos)
            sc = self.rightClickPoint[1] + QPoint(int(PhotoViewer.MOUSEWIDTH/2), int(PhotoViewer.MOUSEWIDTH /2))
            abc = self.mapToScene(sc).toPoint() 
            abc = abc - self.rightClickPoint[0]
            self.screwReal = abc.x() * 2
            self.screwDraw = int (PhotoViewer.MOUSEWIDTH /2 / self.curfactor)
            print("rightinfoclick:"+str(self.screwReal)+"=>"+str(self.screwDraw)+'==>'+str(self.curfactor))
            self.scene().update()
        else:
            print("right no click:"+str(pt.x())+"=>"+str(pt.y()))
            self.rightClickPoint = (QPoint(), QPoint())

    def UpdateImage(self, bmp):
        self.ShowPreImage(bmp)

    def enterEvent(self, event):
        if not self.isPreviewMode:
            QtWidgets.QApplication.setOverrideCursor(self.CURSOR_NEW)

    def leaveEvent(self, event):
        QtWidgets.QApplication.setOverrideCursor(self.CUR_CUESOR)

    def clear(self):
        self.setPhoto(QPixmap())

    def SetCamera(self, which):
        self._camerapoisition = which
        self.logger = logging.getLogger('PSILOG')

    def SetProfile(self, profilename, filename):
        self.profile.profilename = profilename
        self.profile.filename = filename

    # get profile directory sub directory
    def DirSub(self, argument):
        switcher = {
            CAMERA.LEFT: "left",
            CAMERA.TOP: "top",
            CAMERA.RIGHT: "right",
        }
        return switcher.get(argument, "Invalid")

    def setServerProxy(self, value):
        self._client = value

    def ShowPreImage(self, image):
        self._imagepixmap = image
        self.setPhoto(self._imagepixmap)

    def setImageScale(self):
        if self.w == 0 or self.h ==0:
            self.w = self.width()
            self.h = self.height()
            self.logger.info("uigview:"+str(self.w)+"X"+str(self.h))

    def drawForeground(self, painter, rect):        
        if self._empty or self.rightClickPoint[0].isNull():
            return
        pen = QPen(QColor(21, 51, 255))
        pen.setWidth(3)
        painter.setPen(pen)

        for x in self.profilepoints:
            if x.screwDraw > 0:
                painter.drawEllipse(x.centrpoint, x.screwDraw, x.screwDraw)

        painter.drawEllipse(self.rightClickPoint[0], self.screwDraw, self.screwDraw)


    def InitProfile(self):
        self.profilepoints = []
        self.rightClickPoint = (QPoint(),QPoint())
        self.screwDraw = 0
        self.screwReal= 0

    def DrawProfile(self, profilename):
        self.logger.info("DrawImageProfile ++ " + str(self._camerapoisition))
        ret = 0
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

        painterInstance.end()
        self.ShowPreImage(_imagepixmap)
        self.toggleReviewMode(False)
        self.logger.info("DrawImageProfile -- ")
        return ret

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

        #self.setPhoto(self._imagepixmap)
        self.showThreadImageUpdate.emit(self._imagepixmap)
        painterInstance.end()
        self.imagedresult = ret
        self.logger.info("DrawImageResults -- ")
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
                    self.profilepoints.append(ProfilePoint(roi_0,roi_2, roi_1, roi_3))
                    #x = roi_0 + int((roi_1 - roi_0 + 1)/2)
                    #y = roi_2 + int((roi_3 - roi_2 + 1)/2)
                    #centerpoint.append((x,y))

            return True
        
        return False
        

    def AddProfilePoint(self):
        if self.screwReal == 0 or self.screwDraw == 0:
            return
        pt = ProfilePoint(0,0,0,0)
        pt.setCentrSize(self.rightClickPoint[0], self.screwReal, self.screwReal)
        pt.screwDraw = self.screwDraw
        self.profilepoints.append(pt)
        self.screwReal = 0
        self.screwDraw = 0
    
    def fileprechar(self, argument):
        switcher = {
            CAMERA.LEFT: "L",
            CAMERA.TOP: "T",
            CAMERA.RIGHT: "R",
        }
        return switcher.get(argument, "Invalid")


    def _savescrew(self, ptt, _indexscrew):
        if self._imagepixmap is None or self._imagepixmap.isNull():
            return
           
        x = ptt.lefttop.x()
        y = ptt.lefttop.y()
        x1 = ptt.rightbottom.x()
        y1 = ptt.rightbottom.y()
        currentQRect = QRect(QPoint(x,y),QPoint(x1 - 1, y1 - 1))
        cropQPixmap = self._imagepixmap.copy(currentQRect)
        profilepath=os.path.join(self.profilerootpath, self.profile.profilename)
        filename = self.fileprechar(self._camerapoisition)+str(_indexscrew)+".png" 
        profilepath=os.path.join(profilepath, self.DirSub(self._camerapoisition), filename)
        cropQPixmap.save(profilepath)
        #screwpoint = profiledata.screw(self.profile.profilename, filename, ptt.centrpoint, QPoint(x,y), QPoint(x1,y1))
        #self.ProfilePoint.append(screwpoint)
        sinfo = profilepath+", "+str(x)+", "+str(x1)+", "+str(y)+", "+str(y1)
        profiletxt = os.path.join(self.profilerootpath, self.profile.profilename, self.DirSub(self._camerapoisition),  self.profile.profilename+".txt")
        self.append_new_line(profiletxt, sinfo)


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

    def needSaveProfile(self):
        return len(self.profilepoints) > 0

    def SaveProfile(self):
        self.logger.info("SaveProfile ++ ")
        if len(self.profilepoints) == 0:
            return
        index = 0
        profiletxt = os.path.join(self.profilerootpath, self.profile.profilename, self.DirSub(self._camerapoisition),  self.profile.profilename+".txt")
        if os.path.exists(profiletxt):
            os.remove(profiletxt)
        
        rects = []
        if self._client:
            for x in self.profilepoints:
                rects.append([x.lefttop.x(), x.lefttop.y(), x.rightbottom.x(), x.rightbottom.y()])

            self.logger.info(rects)
            self._client.SaveProfile(self._camerapoisition.value, rects)
            for i in range(0,2):
                while True:
                    try:
                        self._client.SaveProfile(self._camerapoisition.value, rects)
                    except Exception as e:
                        self.logger.exception(str(e))
                        time.sleep(0.1)
                        continue
                    break
        else:
            for x in self.profilepoints:
                self._savescrew(x, index)
                index += 1

        self.profilepoints = []
        self.logger.info("SaveProfile -- ")