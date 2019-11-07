# PhoEvent.py
# Contains the different shapes to draw and what they represent (instantaneous events, intervals, etc)
# https://www.e-education.psu.edu/geog489/node/2301
# https://wiki.python.org/moin/PyQt/Making%20non-clickable%20widgets%20clickable

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

class PhoEvent(QObject):

    def __init__(self, startTime=datetime.now(), name='', color=Qt.black, extended_data=dict()):
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


class PhoDurationEvent(PhoEvent):
    InstantaneousEventDuration = timedelta(seconds=2)
    RectCornerRounding = 8
    ColorBase = QColor(51, 204, 255)  # Teal
    ColorEmph = QColor(51, 255, 102)  # Green
    ColorActive = QColor(255, 102, 51)  # Orange

    ColorBorderBase = QColor('#e0e0e0')  # Whiteish
    ColorBorderActive = QColor(255, 222, 122)  # Yellowish

    def __init__(self, startTime=datetime.now(), endTime=None, name='', color=QColor(51, 204, 255), extended_data=dict()):
        super(PhoDurationEvent, self).__init__(startTime, name, color, extended_data)
        self.endTime = endTime

    def __eq__(self, otherEvent):
        return self.name == otherEvent.name and self.startTime == otherEvent.startTime and self.endTime == otherEvent.endTime

    # Less Than (<) operator
    def is_entirely_less_than(self, otherEvent):
        # Returns true if this event is entirely less than the otherEvent (meaning it both starts AND completes before the start of the otherEvent)
        return self.startTime < otherEvent.startTime and self.endTime < otherEvent.startTime

    def is_entirely_greater_than(self, otherEvent):
        # Returns true if this event is entirely greater than the otherEvent (meaning it both starts AND completes after the end of the otherEvent)
        return self.startTime > otherEvent.endTime and self.endTime > otherEvent.endTime


    def overlaps_range(self, range_start_datetime, range_end_datetime):
        # Returns true if the event overlaps a given datetime range
        if self.endTime:
            if (self.endTime < range_start_datetime):
                # It ends prior to the start of the range
                return False
            elif (self.startTime > range_end_datetime):
                # It starts after the end of the range
                return False
            else:
                # It falls within the range
                return True
        else:
            if (self.startTime >= range_start_datetime) and (self.startTime <= range_end_datetime):
                return True
            else:
                return False

    # def overlaps(self, otherEvent):
    #     # Returns true if this event overlaps the otherEvent
    #     if otherEvent.end
    #     return self.

    def __str__(self):
        return 'Event {0}: [startTime: {1}, endTime: {2}], duration: {3}, extended_data: {4}'.format(self.name, self.startTime, self.endTime, self.computeDuration(), str(self.extended_data))

    def computeDuration(self):
        if self.endTime:
            return (self.endTime - self.startTime)
        else:
            return PhoDurationEvent.InstantaneousEventDuration

    # def move(self, deltaX, deltaY):
    #     self.x += deltaX
    #     self.y += deltaY

    def on_button_clicked(self, event):
        self.is_emphasized = False
        self.is_active = True

    def on_button_released(self, event):
        self.is_emphasized = False
        self.is_active = False

    def keyPressEvent(self, event):
        gey = event.key()
        self.func = (None, None)
        if gey == Qt.Key_M:
            print("Key 'm' pressed!")
        elif gey == Qt.Key_Right:
            print("Right key pressed!, call drawFundBlock()")
            # self.func = (self.drawFundBlock, {})
            self.mModified = True
        # elif gey == Qt.Key_5:
        #     print("#5 pressed, call drawNumber()")
        #     self.func = (self.drawNumber, {"notePoint": QPoint(100, 100)})
        #     self.mModified = True

    # Returns the duration of the time relative to this event. As would be used in a media player to determine the playhead time.
    def compute_relative_offset_duration(self, time):
        relative_offset_duration = time - self.startTime
        # percent_duration = relative_offset_duration / self.computeDuration()
        return relative_offset_duration

    # "pass": specifies that we're leaving this method "virtual" or intensionally empty to be overriden by a subclass.
    def paint(self, painter, totalStartTime, totalEndTime, totalDuration, totalParentCanvasRect):
        # "total*" refers to the parent frame in which this event is to be drawn
        # totalStartTime, totalEndTime, totalDuration, totalParentCanvasRect
        percentDuration = (self.computeDuration() / totalDuration)
        offsetStartDuration = self.startTime - totalStartTime
        percentOffsetStart = offsetStartDuration / totalDuration
        x = percentOffsetStart * totalParentCanvasRect.width()
        width = percentDuration * totalParentCanvasRect.width()
        height = totalParentCanvasRect.height()
        y = 0.0
        eventRect = QRect(x, y, width, height)
        # painter.setPen( QtGui.QPen( Qt.darkBlue, 2, join=Qt.MiterJoin ) )

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        if self.is_deemphasized:
            activeColor = Qt.lightGray
        else:
            # de-emphasized overrides emphasized status
            if self.is_emphasized:
                activeColor = PhoDurationEvent.ColorEmph
            else:
                activeColor = self.color

        if self.is_active:
            painter.setPen(QtGui.QPen(PhoDurationEvent.ColorBorderActive, 4.0, join=Qt.MiterJoin))
            painter.setBrush(QBrush(PhoDurationEvent.ColorActive, Qt.SolidPattern))
        else:
            painter.setPen(QtGui.QPen(PhoDurationEvent.ColorBorderBase, 1.5, join=Qt.MiterJoin))
            painter.setBrush(QBrush(activeColor, Qt.SolidPattern))

        if self.endTime is None:
            # Instantaneous type event
            # painter.setPen(Qt.NoPen)
            if self.is_emphasized:
                penWidth = 1.0
            else:
                penWidth = 0.2

            ## NOTE: Apparently for events as small as the instantaneous events (with a width of 2) the "Brush" or "fill" doesn't matter, only the stroke does.
            painter.setPen(QtGui.QPen(activeColor, penWidth, join=Qt.MiterJoin))
            painter.drawRect(x, y, width, height)
        else:
            # Normal duration event (like for videos)
            painter.drawRoundedRect(x, y, width, height, PhoDurationEvent.RectCornerRounding, PhoDurationEvent.RectCornerRounding)
            # If it's not an instantaneous event, draw the label
            painter.drawText(eventRect, Qt.AlignCenter, self.name)

        painter.restore()
        return eventRect

    ## GUI CLASS


