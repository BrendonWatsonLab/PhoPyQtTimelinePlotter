# EventTrackDrawingWidget.py
# Contains EventTrackDrawingWidget which draws several PhoEvent objects as rectangles or lines within a single track.

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget,QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
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
        # self.setToolTip('This is a <b>QWidget</b> widget')
        self.setMouseTracking(True)

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

