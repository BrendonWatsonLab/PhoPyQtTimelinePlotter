# EventTrackDrawingWidget.py
# Contains EventTrackDrawingWidget which draws several PhoEvent objects as rectangles or lines within a single track.

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget,QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QLinearGradient
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidgetBase import TimelineTrackDrawingWidgetBase, ItemSelectionOptions
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_EventsBase import TimelineTrackDrawingWidget_EventsBase

class TimelineTrackDrawingWidget_Videos(TimelineTrackDrawingWidget_EventsBase):
    # This defines a signal called 'hover_changed'/'selection_changed' that takes the trackID and the index of the child object that was hovered/selected
    default_shouldDismissSelectionUponMouseButtonRelease = True
    default_itemSelectionMode = ItemSelectionOptions.MultiSelection

    def __init__(self, trackID, durationObjects, instantaneousObjects, totalStartTime, totalEndTime, database_connection, parent=None, wantsKeyboardEvents=True, wantsMouseEvents=True):
        super(TimelineTrackDrawingWidget_Videos, self).__init__(trackID, durationObjects, instantaneousObjects, totalStartTime, totalEndTime, database_connection=database_connection, parent=parent, wantsKeyboardEvents=wantsKeyboardEvents, wantsMouseEvents=wantsMouseEvents)
        self.currNowPlayingVideoIndicies = []

    def set_now_playing(self, videoObjectIndex):
        if self.currNowPlayingVideoIndicies.__contains__(videoObjectIndex):
            # already playing, just return
            print("video with index {0} is already playing!".format(videoObjectIndex))
            return

        # Set other videos to not now_playing
        for aPreviousPlayingVideoIndex in self.currNowPlayingVideoIndicies:
            self.durationObjects[aPreviousPlayingVideoIndex].set_is_playing(False)

        # Set new video to now_playing
        self.durationObjects[videoObjectIndex].set_is_playing(True)
        self.currNowPlayingVideoIndicies.append(videoObjectIndex)

        return

