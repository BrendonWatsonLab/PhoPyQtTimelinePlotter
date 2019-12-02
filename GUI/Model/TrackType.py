import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget,QTableWidgetItem, QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QPalette, QLinearGradient
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize
from enum import Enum

## IMPORT:
# from GUI.Model.TrackType import TrackType

class TrackType(Enum):
    Unknown = 1
    Video = 2
    Annotation = 3
    Partition = 4

    def get_short_str(self):
        if self == TrackType.Unknown:
            return '?'
        elif self == TrackType.Video:
            return 'V'
        elif self == TrackType.Annotation:
            return 'A'
        elif self == TrackType.Partition:
            return 'P'
        else:
            return '!'

    def get_medium_str(self):
        if self == TrackType.Unknown:
            return '???'
        elif self == TrackType.Video:
            return 'Vid'
        elif self == TrackType.Annotation:
            return 'Note'
        elif self == TrackType.Partition:
            return 'Part'
        else:
            return 'ERR'

    def get_long_str(self):
        if self == TrackType.Unknown:
            return 'Unknown'
        elif self == TrackType.Video:
            return 'Video'
        elif self == TrackType.Annotation:
            return 'Annotation'
        elif self == TrackType.Partition:
            return 'Partition'
        else:
            return 'ERROR'

    def __str__(self):
        return self.get_long_str()
