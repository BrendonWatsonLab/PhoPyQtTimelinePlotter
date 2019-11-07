# EventTrackDrawingWidget.py
# Contains EventTrackDrawingWidget which draws several PhoEvent objects as rectangles or lines within a single track.

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget,QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidgetBase import *

class TimelineTrackDrawingWidget_Events(TimelineTrackDrawingWidgetBase):
    # This defines a signal called 'hover_changed'/'selection_changed' that takes the trackID and the index of the child object that was hovered/selected
    shouldDismissSelectionUponMouseButtonRelease = True

    def __init__(self, trackID, durationObjects, instantaneousObjects, totalStartTime, totalEndTime):
        super(TimelineTrackDrawingWidget_Events, self).__init__(trackID, totalStartTime, totalEndTime)
        self.durationObjects = durationObjects
        self.instantaneousObjects = instantaneousObjects
        self.eventRect = np.repeat(QRect(0,0,0,0), len(durationObjects))
        self.instantaneousEventRect = np.repeat(QRect(0,0,0,0), len(instantaneousObjects))
        # Hovered Object
        self.hovered_object_index = None
        self.hovered_object = None
        self.hovered_object_rect = None
        # Selected Object
        self.selected_object_index = None

    
    def paintEvent( self, event ):
        qp = QtGui.QPainter()
        qp.begin( self )
        # TODO: minor speedup by re-using the array of QRect objects if the size doesn't change
        self.eventRect = np.repeat(QRect(0,0,0,0), len(self.durationObjects))
        self.instantaneousEventRect = np.repeat(QRect(0, 0, 0, 0), len(self.instantaneousObjects))

        # Draw the trace cursor
        # qp.setPen(QtGui.QPen(EventsDrawingWindow.TraceCursorColor, 20.0, join=Qt.MiterJoin))
        # qp.drawRect(event.rect().x(), event.rect().y(), EventsDrawingWindow.TraceCursorWidth, self.height())

        # Draw the duration objects
        for (index, obj) in enumerate(self.durationObjects):
            self.eventRect[index] = obj.paint( qp, self.totalStartTime, self.totalEndTime, self.totalDuration, event.rect())
        # Draw the instantaneous event objects
        for (index, obj) in enumerate(self.instantaneousObjects):
            self.instantaneousEventRect[index] = obj.paint(qp, self.totalStartTime, self.totalEndTime, self.totalDuration, event.rect())

        qp.end()

    # Returns the index of the child object that the (x, y) point falls within, or None if it doesn't fall within an event.
    def find_child_object(self, event_x, event_y):
        clicked_object_index = None
        for (index, aRect) in enumerate(self.eventRect):
            if aRect.contains(event_x, event_y):
                clicked_object_index = index
                break
        return clicked_object_index

    def set_active_filter(self, start_datetime, end_datetime):
        # Draw the duration objects
        for (index, obj) in enumerate(self.durationObjects):
            obj.is_deemphasized = not obj.overlaps_range(start_datetime, end_datetime)
        # Draw the instantaneous event objects
        for (index, obj) in enumerate(self.instantaneousObjects):
            obj.is_deemphasized = not obj.overlaps_range(start_datetime, end_datetime)
        self.update()

    def on_button_clicked(self, event):
        self.selected_object_index = self.find_child_object(event.x(), event.y())

        if self.selected_object_index is None:
            self.selection_changed.emit(self.trackID, -1)
        else:
            self.durationObjects[self.selected_object_index].on_button_clicked(event)
            self.update()
            self.selection_changed.emit(self.trackID, self.selected_object_index)

    def on_button_released(self, event):
        # Check if we want to dismiss the selection when the mouse button is released (requiring the user to hold down the button to see the results)
        if TimelineTrackDrawingWidget_Events.shouldDismissSelectionUponMouseButtonRelease:
            self.selected_object_index = self.find_child_object(event.x(), event.y())

            if self.selected_object_index is None:
                self.selection_changed.emit(self.trackID, -1)
            else:
                self.durationObjects[self.selected_object_index].on_button_released(event)
                self.selection_changed.emit(self.trackID, self.selected_object_index)
                self.update()

    def keyPressEvent(self, event):
        gey = event.key()
        self.func = (None, None)
        if gey == Qt.Key_M:
            print("Key 'm' pressed!")
        elif gey == Qt.Key_Right:
            print("Right key pressed!, call drawFundBlock()")
            self.func = (self.drawFundBlock, {})
            self.mModified = True
            self.update()
            self.nextRegion()
        elif gey == Qt.Key_5:
            print("#5 pressed, call drawNumber()")
            self.func = (self.drawNumber, {"notePoint": QPoint(100, 100)})
            self.mModified = True
            self.update()

    def on_mouse_moved(self, event):
        self.hovered_object_index = self.find_child_object(event.x(), event.y())
        if self.hovered_object_index is None:
            # No object hovered
            QToolTip.hideText()
            self.hovered_object = None
            self.hovered_object_rect = None
            self.hover_changed.emit(self.trackID, -1)
        else:
            self.hovered_object = self.durationObjects[self.hovered_object_index]
            self.hovered_object_rect = self.eventRect[self.hovered_object_index]
            text = "event: {0}\nstart_time: {1}\nend_time: {2}\nduration: {3}".format(self.hovered_object.name, self.hovered_object.startTime, self.hovered_object.endTime, self.hovered_object.computeDuration())
            QToolTip.showText(event.globalPos(), text, self, self.hovered_object_rect)
            self.hover_changed.emit(self.trackID, self.hovered_object_index)


