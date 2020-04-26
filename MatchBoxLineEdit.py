from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLineEdit, QHBoxLayout)
from PyQt5.QtCore import pyqtSlot,Qt, QThread, pyqtSignal
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent

import subprocess
import logging
#import time

class MatchBoxLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super(QLineEdit, self).__init__()
        #self.embed_window = QtGui.QWindow()
        #self.embed_widget = QtWidgets.QWidget()
        #MatchBoxLineEdit.createKeyboard()
        #self.embed(MatchBoxLineEdit.keyboardID)
        #self.hashow=False
        #self.parentshow=None

'''
    @staticmethod
    def createKeyboard():
        if MatchBoxLineEdit.keyboardID == 0:
            p = subprocess.Popen(["matchbox-keyboard", "--xid"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            MatchBoxLineEdit.keyboardID = int(p.stdout.readline())

    def embed(self, win_id):
        logging.debug("capturing window 0x%x ", win_id)
        self.embed_window = QtGui.QWindow.fromWinId(win_id)
        self.embed_widget = QtWidgets.QWidget.createWindowContainer(self.embed_window)
        self.infoWindow2 = QDialog(parent=self)
        self.embed_widget.setMinimumWidth(600)
        self.embed_widget.setMinimumHeight(300)
        rect = self.geometry()
        #self.infoWindow2.setGeometry(rect.x()+rect.width(), rect.y()+rect.height(), 400, 300)
        self.move(rect.x()+rect.width(), rect.y()+rect.height())
        self.hbox2 = QHBoxLayout()
        self.hbox2.addWidget(self.embed_widget)
        self.infoWindow2.setLayout(self.hbox2)

        #self.embed_widget.show()
        #self.setWidget(self.embed_widget)

    def focusInEvent(self, e):
        pass
        #try:
            #subprocess.Popen(["matchbox-keyboard"])
            #self.embed(MatchBoxLineEdit.keyboardID)
            #if not MatchBoxLineEdit.hashow:
            #self.infoWindow2.show()
            #self.infoWindow2.exec_()
            #MatchBoxLineEdit.hashow=True
            #time.sleep(1)
            #win = subprocess.check_output(['xdotool', 'getactivewindow']).strip()
            #subprocess.check_call(['xdotool','windowsize',win, '640','480'])
            #subprocess.check_call(['xdotool','windowmove',win, str(self.x()), str(self.y()+40)])
        #except FileNotFoundError:
        #    pass
    
    def focusOutEvent(self,e):
        #subprocess.Popen(["killall","matchbox-keyboa"])
        #self.infoWindow2.hide()
        #MatchBoxLineEdit.hashow= False
        pass
'''