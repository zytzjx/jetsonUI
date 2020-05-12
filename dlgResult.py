from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QApplication, QDialog, QDesktopWidget, QTableWidgetItem)
from PyQt5.QtGui import  QColor, QBrush
from PyQt5.uic import loadUi

class ResultDialog(QDialog):
    def __init__(self, data,  parent=None):
        super(ResultDialog, self).__init__()
        loadUi('dlgResult.ui', self)
        #self.changeStyle('Fusion')
        self.center()
        self.setWindowFlags(Qt.WindowMinimizeButtonHint  | Qt.WindowTitleHint | Qt.FramelessWindowHint)
        self.setWindowTitle("PSI Result")
        self.pbExit.clicked.connect(self.close)
        self.tableWidget.verticalHeader().setVisible(False)
        self.data = data
        self.ShowData()

    def center(self):
        # geometry of the main window
        qr = self.frameGeometry()

        # center point of screen
        cp = QDesktopWidget().availableGeometry().center()

        # move rectangle's center point to screen's center point
        qr.moveCenter(cp)

        # top left of rectangle becomes top left of window centering it
        self.move(qr.topLeft())

    def Value2Str(self, status):
        if status==0:
            return "Success", Qt.green
        elif status==1:
            return "Warning", Qt.yellow
        else:
            return "Error", Qt.red

    def CreateCell(self, d):
        a, b = self.Value2Str(d)
        item = QTableWidgetItem(a)
        item.setForeground(QBrush(b))
        return item

    def ShowData(self):
        self.tableWidget.setRowCount(len(self.data))
        self.tableWidget.setColumnCount(4)
        index = 0
        for dd in self.data:
            self.tableWidget.setItem(index,0, QTableWidgetItem(str(index+1)))
            self.tableWidget.setItem(index,1, self.CreateCell(dd[0]))
            self.tableWidget.setItem(index,2, self.CreateCell(dd[1]))
            self.tableWidget.setItem(index,3, self.CreateCell(dd[2]))
            index += 1
