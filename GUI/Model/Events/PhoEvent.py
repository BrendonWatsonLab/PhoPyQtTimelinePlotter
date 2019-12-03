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

    DefaultOpacity = 200 # Fill opacity, specified as an integer 0-255
    ActiveOpacity = 220
    DeEmphOpacity = 160

    on_info = pyqtSignal(int)
    on_edit = pyqtSignal(int)
    on_delete = pyqtSignal(int)

    on_create_marker_at_start = pyqtSignal(int, datetime)
    on_create_marker_at_end = pyqtSignal(int, datetime)

    def __init__(self, startTime=datetime.now(), name='', color=Qt.black, extended_data=dict(), parent=None):
        super(PhoEvent, self).__init__(parent)
        self.name = name
        self.startTime = startTime
        self.color = color
        self.is_deemphasized = False
        self.is_emphasized = False
        self.is_active = False
        self.extended_data = extended_data

    # gets the child index that's set by the parent with "newAnnotationView.setAccessibleName(str(newAnnotationIndex))"
    def get_track_index(self):
        curr_name = self.accessibleName()
        return int(curr_name)

        
    def __eq__(self, otherEvent):
        return self.name == otherEvent.name and self.startTime == otherEvent.startTime

    # Less Than (<) operator
    def __lt__(self, otherEvent):
        return self.startTime < otherEvent.startTime

    def __str__(self):
        return 'Event {0}: startTime: {1}, color: {2}, extended_data: {3}'.format(self.name, self.startTime, self.color, str(self.extended_data))


    def set_state_selected(self):
        self.is_emphasized = False
        self.is_active = True

    def set_state_deselected(self):
        self.is_emphasized = False
        self.is_active = False

    def set_state_emphasized(self):
        self.is_emphasized = True

    def set_state_deemphasized(self):
        self.is_emphasized = False

    # def move(self, deltaX, deltaY):
    #     self.x += deltaX
    #     self.y += deltaY

    def on_button_clicked(self, event):
        pass

    def on_button_released(self, event):
        pass

    def on_key_pressed(self, event):
        pass

    def get_fill_color(self):
        pass
    
    # "pass": specifies that we're leaving this method "virtual" or intensionally empty to be overriden by a subclass.
    def paint(self, painter, totalDuration, totalParentCanvasRect):
        pass

