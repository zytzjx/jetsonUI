#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Py40 PyQt5 tutorial 

In this example, we create a bit
more complicated window layout using
the QGridLayout manager. 

author: Jan Bodnar
website: py40.com 
last edited: January 2015
"""
'''
import os
import threading
import sys
import subprocess
import logging
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, 
    QTextEdit, QGridLayout, QApplication)
from PyQt5 import QtCore, QtGui

class TestLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super(QLineEdit, self).__init__()

    def focusInEvent(self, e):
        pass
        # subprocess.Popen(["/usr/local/bin/matchbox-keyboard"])


    def focusOutEvent(self,e):
        pass
        # subprocess.Popen(["pkill","matchbox-keyboard"])

class Example(QWidget):
    
    def __init__(self):
        super().__init__()
        self.initUI()
        
        
    def initUI(self):
        title = QLabel('Title')
        author = QLabel('Author')
        review = QLabel('Review')

        titleEdit = QLineEdit()
        authorEdit = QLineEdit()
        reviewEdit = TestLineEdit()

        grid = QGridLayout()
        grid.setSpacing(10)

        grid.addWidget(title, 1, 0)
        grid.addWidget(titleEdit, 1, 1)

        grid.addWidget(author, 2, 0)
        grid.addWidget(authorEdit, 2, 1)

        grid.addWidget(review, 3, 0)
        grid.addWidget(reviewEdit, 3, 1, 5, 1)
        
        self.setLayout(grid) 
        
        self.setGeometry(300, 300, 350, 300)
        self.setWindowTitle('Review')    
        # return grid
        # self.show()
        
def add_kb():
    p = subprocess.Popen(["matchbox-keyboard", "--xid"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    id = int(p.stdout.readline())
    window = QtGui.QWindow.fromWinId(id)
    widget = QWidget.createWindowContainer(window)
    widget.setMinimumWidth(600)
    widget.setMinimumHeight(300)
    return widget

        
if __name__ == '__main__':    
    app = QApplication(sys.argv)
    ex = Example()
    grid =ex.findChildren(QGridLayout)
    w = add_kb()
    grid[0].addWidget(w)
    # ex.show()
    ex.showFullScreen()
    ret = app.exec_()
    subprocess.Popen(["pkill","matchbox-keyboard"])
    sys.exit(ret)
'''

import sys
from PyQt5.QtWidgets import (QWidget, QApplication, QMainWindow, QTextEdit, QDockWidget, QListWidget)
from PyQt5.QtCore import Qt
from PyQt5 import QtCore, QtGui

import os
import threading
import sys
import subprocess
import logging

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.resize(800, 600)

        dockWidget = QDockWidget('Dock', self)

        self.textEdit = QTextEdit()
        self.textEdit.setFontPointSize(16)

        self.listWidget = QListWidget()
        self.listWidget.addItem('Google')
        self.listWidget.addItem('Facebook')
        self.listWidget.addItem('Microsoft')
        self.listWidget.addItem('Apple')
        self.listWidget.itemDoubleClicked.connect(self.get_list_item)

        p = subprocess.Popen(["matchbox-keyboard", "--xid"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        id = int(p.stdout.readline())
        window = QtGui.QWindow.fromWinId(id)
        widget = QWidget.createWindowContainer(window)
        widget.setMinimumWidth(600)
        widget.setMinimumHeight(300)


        dockWidget.setWidget(widget)
        dockWidget.setFloating(False)

        self.setCentralWidget(self.textEdit)
        self.addDockWidget(Qt.RightDockWidgetArea, dockWidget)

    def get_list_item(self):
        self.textEdit.setPlainText(self.listWidget.currentItem().text())
    



    def add_kb(self):
        p = subprocess.Popen(["matchbox-keyboard", "--xid"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        id = int(p.stdout.readline())
        window = QtGui.QWindow.fromWinId(id)
        widget = QWidget.createWindowContainer(window)
        widget.setMinimumWidth(600)
        widget.setMinimumHeight(300)
        return widget


if __name__ == '__main__':
	app = QApplication(sys.argv)

	window = MainWindow()
	window.show()

	sys.exit(app.exec_())
'''

def get_window_id(name):
    import Xlib.display

    d = Xlib.display.Display()
    r = d.screen().root

    window_ids = r.get_full_property(
        d.intern_atom('_NET_CLIENT_LIST'), Xlib.X.AnyPropertyType
    ).value

    for window_id in window_ids:
        window = d.create_resource_object('window', window_id)
        if window.get_wm_name() == name:
            return window_id


def run_app(window_id):
    from PyQt5.QtGui import QWindow
    from PyQt5.QtWidgets import QWidget, QVBoxLayout, QApplication, QPushButton

    app = QApplication([])
    main_widget = QWidget()
    layout = QVBoxLayout(main_widget)

    window = QWindow.fromWinId(window_id)
    widget = QWidget.createWindowContainer(window)
    layout.addWidget(widget)

    button = QPushButton('Close')
    button.clicked.connect(main_widget.close)
    layout.addWidget(button)

    main_widget.show()
    app.exec_()


if __name__ == '__main__':
    window_id = get_window_id('Keyboard')
    if window_id:
        run_app(window_id)

'''