# EventTrackDrawingWidget.py
# Contains EventTrackDrawingWidget which draws several PhoEvent objects as rectangles or lines within a single track.

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget,QTableWidgetItem, QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QPalette, QLinearGradient
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize, pyqtSlot
from enum import Enum

from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingWidget
from GUI.UI.UIState import ItemInteractionState, ItemHoverState, ItemSelectionState
from GUI.Helpers.FixedTimelineContentsWidthMixin import FixedTimelineContentsWidthMixin
from GUI.Helpers.DateTimeRenders import DateTimeRenderMixin


class ItemSelectionOptions(Enum):
        DisableSelection = 1 # disallows selection
        SingleSelection = 2 #  allows one or no items to be selected
        # TODO: could have a "RequireSingleSelection" which disallows deselection
        MultiSelection = 3  # allows multiple selection

# The base timeline track widget which all others should inherit from
class TimelineTrackDrawingWidgetBase(DateTimeRenderMixin, FixedTimelineContentsWidthMixin, AbstractDatabaseAccessingWidget):
    # This defines a signal called 'hover_changed'/'selection_changed' that takes the trackID and the index of the child object that was hovered/selected
    hover_changed = pyqtSignal(int, int, name='hover_changed')
    selection_changed = pyqtSignal(int, int, name='selection_changed')

    on_create_marker = pyqtSignal(datetime)
    
    static_TimeTrackObjectIndex_NoSelection = -1  # The integer value that indicates no object has been selected in the timeline

    def __init__(self, trackID, totalStartTime, totalEndTime, database_connection, parent=None, wantsKeyboardEvents=False, wantsMouseEvents=True):
        super(TimelineTrackDrawingWidgetBase, self).__init__(database_connection, parent)
        self.trackID = trackID
        self.totalStartTime = totalStartTime
        self.totalEndTime = totalEndTime
        self.totalDuration = (self.totalEndTime - self.totalStartTime)
        self.fixedWidth = 800.0
        
        self.wantsKeyboardEvents = wantsKeyboardEvents
        self.wantsMouseEvents = wantsMouseEvents
        
        self.trackLabelText = None

        QToolTip.setFont(QFont('SansSerif', 10))

        self.trackInteractionState = ItemInteractionState(ItemHoverState.Default, ItemSelectionState.Default, parent=self)
        
        # # Debug background fill
        # p = self.palette()
        # p.setColor(QPalette.Background, Qt.red)
        # self.setAutoFillBackground(True)
        # self.setPalette(p)

        # self.setToolTip('This is a <b>QWidget</b> widget')

        # Setup input events
        if (self.wantsKeyboardEvents):
            self.keyPressEvent = self.on_key_pressed
            self.keyReleaseEvent = self.on_key_released

        self.setMouseTracking(self.wantsMouseEvents)
        if (self.wantsMouseEvents):
            self.mousePressEvent = self.on_button_clicked
            self.mouseReleaseEvent = self.on_button_released
            self.mouseMoveEvent = self.on_mouse_moved


    def get_trackID(self):
        return self.trackID
        
    def set_track_title_label(self, title):
        self.trackLabelText = title

    def get_track_title_label(self):
        return self.trackLabelText
        
    def paintEvent( self, event ):
        pass

    def get_background_gradient(self, height):
        middleColor = QColor(40,40,40,64)
        edgeColor = QColor(38,38,38,255)
        transitionColor = QColor(255,255,255,200)
        innerGlowColor = QColor(255,255,255,64)

        if (self.is_track_emphasized()):
            brightnessAmount = 160 # returns a color that's 60% brighter
            middleColor = middleColor.lighter(brightnessAmount) 
            edgeColor = edgeColor.lighter(brightnessAmount)
            transitionColor = transitionColor.lighter(brightnessAmount)
            innerGlowColor = innerGlowColor.lighter(brightnessAmount)


        gradientKeysMain = [(0.09, edgeColor),(0.095, transitionColor),(0.1, innerGlowColor), (0.16, middleColor),
        (0.84, middleColor),(0.9, innerGlowColor),(0.905, transitionColor), (0.91, edgeColor)]

        # Draw the linear horizontal gradient.
        out_gradient = QLinearGradient(0, 0, 0, height)
        for stop, color in gradientKeysMain:
            out_gradient.setColorAt(stop, QColor(color))

        return out_gradient

    def is_track_emphasized(self):
        return self.trackInteractionState.is_emphasized()

    def is_track_selected(self):
        return self.trackInteractionState.is_selected()
    
    def deselect_all(self):
        pass

    def select(self, new_selection_index):
        pass

    def deselect(self, selection_index):
        pass

    def deemphasize_all(self):
        pass

    def emphasize(self, new_emph_index):
        pass

    def deemphasize(self, emph_index):
        pass

    def on_button_clicked(self, event):
        pass

    def on_button_released(self, event):
        pass

    def on_key_pressed(self, event):
        pass

    def on_key_released(self, event):
        pass

    def on_mouse_moved(self, event):
        pass

    def get_is_under_mouse(self):
        return self.underMouse()

    # Timeline position/time converion functions:
    # Get scale from length
    # def getScale(self):
    #     return float(self.totalDuration)/float(self.width())

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

    def percent_to_offset(self, percent_offset):
        event_x = percent_offset * self.width()
        return event_x

    def duration_to_offset(self, duration_offset):
        percent_x = duration_offset / self.totalDuration
        event_x = self.percent_to_offset(percent_x)
        return event_x

    def datetime_to_offset(self, newDatetime):
        duration_offset = newDatetime - self.totalStartTime
        event_x = self.duration_to_offset(duration_offset)
        return event_x

    def enterEvent(self, QEvent):
        # print("TimelineTrackDrawingWidgetBase.enterEvent(...): track_id: {0}".format(self.trackID))
        self.trackInteractionState.set_hover_state(ItemHoverState.Emphasized)
        self.update()
        return QWidget.enterEvent(self, QEvent)

    def leaveEvent(self, QEvent):
        # print("TimelineTrackDrawingWidgetBase.leaveEvent(...): track_id: {0}".format(self.trackID))
        self.trackInteractionState.set_hover_state(ItemHoverState.Default)
        self.update()
        return QWidget.leaveEvent(self, QEvent)