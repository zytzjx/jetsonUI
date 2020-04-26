from PyQt5.QtCore import Qt,QPoint
from dataclasses import dataclass

@dataclass
class profile:
    profilename=""
    filename=""

    def __init__(self, profilename, filename):
        self.profilename = profilename
        self.filename = filename

@dataclass
class screw:
    profilename=""
    filename=""
    Centerpoint= QPoint()
    lefttop=QPoint
    rightbottom=QPoint

    def __init__(self, profilename, filename, cp, lt, rb):
        self.profilename = profilename
        self.filename = filename    
        self.Centerpoint = cp
        self.lefttop = lt
        self.rightbottom = rb


