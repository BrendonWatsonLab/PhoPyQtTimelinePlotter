# PhoEvent.py
# Contains the different shapes to draw and what they represent (instantaneous events, intervals, etc)
# https://www.e-education.psu.edu/geog489/node/2301
# https://wiki.python.org/moin/PyQt/Making%20non-clickable%20widgets%20clickable

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem, QMenu
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QFontMetrics
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

from GUI.Model.Events.PhoDurationEvent import *

## IMPORT:
# from GUI.Model.Events.PhoDurationEvent_Video import PhoDurationEvent_Video

class PhoDurationEvent_Video(PhoDurationEvent):
    
    ColorFillIsPlayingIndicator = QColor(90, 90, 220)  # Bluish
    ColorBorderIsPlayingIndicator = QColor('#e0e0e0')  # Whiteish
    IsPlayingIndicatorBorderWidth = 2
    IsPlayingIndicatorFractionOfHeight = 0.08

    def __init__(self, startTime, endTime, name='', color=QColor(51, 204, 255), extended_data=dict(), parent=None):
        super(PhoDurationEvent_Video, self).__init__(startTime, endTime, name, color, extended_data, parent=parent)
        self.isPlayingVideo = False

    def set_is_playing(self, new_is_playing_state):
        self.isPlayingVideo = new_is_playing_state
        self.update()

    def get_video_url(self):
        return self.extended_data['path']

    # Sets the painter's config based on the current object's state (active, emphasized, deemph, etc)
    def set_painter_config(self, aPainter):
        super().set_painter_config(aPainter)
        return


    # "pass": specifies that we're leaving this method "virtual" or intensionally empty to be overriden by a subclass.
    def paint(self, painter, totalStartTime, totalEndTime, totalDuration, totalParentCanvasRect):
        self.finalEventRect = super().paint(painter, totalStartTime, totalEndTime, totalDuration, totalParentCanvasRect)
        x = self.finalEventRect.x()
        y = self.finalEventRect.y()
        width = self.finalEventRect.width()
        height = self.finalEventRect.height()

        # Draw the rounded-rectangular "now-playing" indicator on the top of the video if needed
        if (self.isPlayingVideo):
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)

            # Add an extra highlight border
            currPenWidth = PhoDurationEvent_Video.IsPlayingIndicatorBorderWidth
            currFillColor = PhoDurationEvent_Video.ColorFillIsPlayingIndicator
            currPenColor = PhoDurationEvent_Video.ColorFillIsPlayingIndicator
            currActivePen = QtGui.QPen(currPenColor, currPenWidth, join=Qt.MiterJoin)
            currActiveBrush = QBrush(currFillColor, Qt.SolidPattern)
            painter.setPen(currActivePen)
            painter.setBrush(currActiveBrush)

            nowPlayingIndicatorHeight = PhoDurationEvent_Video.IsPlayingIndicatorFractionOfHeight * height

            painter.drawRoundedRect(x, y, width, nowPlayingIndicatorHeight, PhoDurationEvent_Video.RectCornerRounding, PhoDurationEvent_Video.RectCornerRounding)

            painter.restore()

        return self.finalEventRect

    ## GUI CLASS


