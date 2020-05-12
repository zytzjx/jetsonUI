from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QDialog, QStyleFactory, QLineEdit, QFileDialog, QMessageBox)
from PyQt5.QtGui import QIcon, QPixmap, QImage, QPainter,QPen,QCursor,QMouseEvent
from PyQt5.uic import loadUi

class LoginDialog(QDialog):
    def __init__(self, parent=None):
        super(LoginDialog, self).__init__()
        loadUi('login.ui', self)
        #self.changeStyle('Fusion')
        self.setWindowFlags(Qt.WindowMinimizeButtonHint  | Qt.WindowTitleHint | Qt.FramelessWindowHint)
        self.setWindowTitle("PSI login")
        screenGeometry = QApplication.desktop().screenGeometry()
        x = screenGeometry.width() - self.width() - 10
        y = (screenGeometry.height() - self.height()) / 2
        self.move(x, y)
        self.lePassword.setEchoMode(QLineEdit.Password)
        self.pbClose.clicked.connect(self.close)
        self.pbCancel.clicked.connect(self.close)
        self.pbLogin.clicked.connect(self.On_login)
        self.lePassword.returnPressed.connect(self.On_login)
        self.leUserName.returnPressed.connect(self.focusNextChild)

    def On_login(self):
        if (self.leUserName.text() == 'admin' and
            self.lePassword.text() == 'admin'):
            self.accept()   
        else:
            QMessageBox.warning(
                self, 'Error', 'Bad user or password')    
