# PhoEvent.py
# Contains the different shapes to draw and what they represent (instantaneous events, intervals, etc)
# https://www.e-education.psu.edu/geog489/node/2301
# https://wiki.python.org/moin/PyQt/Making%20non-clickable%20widgets%20clickable

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QWidget, QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

class PhoEvent(QWidget):

    def __init__(self, startTime=datetime.now(), name='', color=Qt.black, extended_data=dict(), parent=None):
        super(PhoEvent, self).__init__(parent)
        self.name = name
        self.startTime = startTime
        self.color = color
        self.is_deemphasized = False
        self.is_emphasized = False
        self.is_active = False
        self.extended_data = extended_data

    def __eq__(self, otherEvent):
        return self.name == otherEvent.name and self.startTime == otherEvent.startTime

    # Less Than (<) operator
    def __lt__(self, otherEvent):
        return self.startTime < otherEvent.startTime

    def __str__(self):
        return 'Event {0}: startTime: {1}, color: {2}, extended_data: {3}'.format(self.name, self.startTime, self.color, str(self.extended_data))

    # def move(self, deltaX, deltaY):
    #     self.x += deltaX
    #     self.y += deltaY

    def on_button_clicked(self, event):
        pass

    def on_button_released(self, event):
        pass

    def keyPressEvent(self, event):
        pass

    # "pass": specifies that we're leaving this method "virtual" or intensionally empty to be overriden by a subclass.
    def paint(self, painter, totalDuration, totalParentCanvasRect):
        pass

