import sys
from datetime import datetime, timezone, timedelta
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QPoint, QLine, QRect, QRectF, pyqtSignal, pyqtSlot, QObject, QMargins
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPalette, QPen, QPolygon, QPainterPath, QPixmap
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea, QVBoxLayout, QGridLayout, QListWidget
import os

# ReferenceMarker.py

"""
RepresentedTimeRange: on object that holds a reference to the current global start and end times
"""
class RepresentedTimeRange(QObject):

    timesChanged = pyqtSignal(datetime, datetime, timedelta) # Called when the timeline's global displayed start/end times are updated
    
    def __init__(self, totalStartTime, totalEndTime, parent=None):
        super(RepresentedTimeRange, self).__init__(parent=parent)
        self._totalStartTime = totalStartTime
        self._totalEndTime = totalEndTime
        self._totalDuration = (totalEndTime - totalStartTime)

    # Getters:
    @property
    def totalStartTime(self):
        return self._totalStartTime

    @property
    def totalEndTime(self):
        return self._totalEndTime

    @property
    def totalDuration(self):
        return (self.totalEndTime - self.totalStartTime)

    # Setters:
    @totalStartTime.setter
    def totalStartTime(self, new_value):
        if self._totalStartTime != new_value:
            self._totalStartTime = new_value
            self.timesChanged.emit(self.totalStartTime, self.totalEndTime, self.totalDuration)
        else:
            # Otherwise nothing has changed
            pass

    @totalEndTime.setter
    def totalEndTime(self, new_value):
        if self._totalEndTime != new_value:
            self._totalEndTime = new_value
            self.timesChanged.emit(self.totalStartTime, self.totalEndTime, self.totalDuration)
        else:
            # Otherwise nothing has changed
            pass


