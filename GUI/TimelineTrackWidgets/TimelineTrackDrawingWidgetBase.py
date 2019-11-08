# EventTrackDrawingWidget.py
# Contains EventTrackDrawingWidget which draws several PhoEvent objects as rectangles or lines within a single track.

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget,QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QPalette
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

# The base timeline track widget which all others should inherit from
class TimelineTrackDrawingWidgetBase(QtWidgets.QWidget):
    # This defines a signal called 'hover_changed'/'selection_changed' that takes the trackID and the index of the child object that was hovered/selected
    hover_changed = pyqtSignal(int, int, name='hover_changed')
    selection_changed = pyqtSignal(int, int, name='selection_changed')

    def __init__(self, trackID, totalStartTime, totalEndTime):
        super(TimelineTrackDrawingWidgetBase, self).__init__()
        self.trackID = trackID
        self.totalStartTime = totalStartTime
        self.totalEndTime = totalEndTime
        self.totalDuration = (self.totalEndTime - self.totalStartTime)
        
        QToolTip.setFont(QFont('SansSerif', 10))
        
        # Debug background fill
        p = self.palette()
        p.setColor(QPalette.Background, Qt.red)
        self.setAutoFillBackground(True)
        self.setPalette(p)
        # self.setToolTip('This is a <b>QWidget</b> widget')
        self.setMouseTracking(True)

        self.mousePressEvent = self.on_button_clicked
        self.mouseReleaseEvent = self.on_button_released

    def minimumSizeHint(self) -> QSize:
        return QSize(500, 50)

    def sizeHint(self) -> QSize:
        return QSize(800, 100)

    def paintEvent( self, event ):
        pass
 
    def on_button_clicked(self, event):
        pass

    def on_button_released(self, event):
        pass

    def keyPressEvent(self, event):
        pass

    def on_mouse_moved(self, event):
        pass

    # Timeline position/time converion functions:
    def offset_to_percent(self, event_x, event_y):
        percent_x = event_x / self.width()
        percent_y = event_y / self.height()
        return (percent_x, percent_y)

    def offset_to_duration(self, event_x):
        (percent_x, percent_y) = self.offset_to_percent(event_x, 0.0)
        return (self.totalDuration * percent_x)

    def offset_to_datetime(self, event_x):
        duration_offset = self.offset_to_duration(event_x)
        return (self.totalStartTime + duration_offset)