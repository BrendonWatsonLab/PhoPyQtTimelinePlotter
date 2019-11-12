# PhoEvent.py
# Contains the different shapes to draw and what they represent (instantaneous events, intervals, etc)
# https://www.e-education.psu.edu/geog489/node/2301
# https://wiki.python.org/moin/PyQt/Making%20non-clickable%20widgets%20clickable

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QPainterPath, QPolygon, QFontMetrics
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

from GUI.Model.PhoEvent import *
from GUI.Model.PhoDurationEvent import *

from GUI.UI.TrianglePainter import *


class PhoDurationEvent_AnnotationComment(PhoDurationEvent):
    InstantaneousEventDuration = timedelta(minutes=30)
    RectCornerRounding = 2
    ColorBase = QColor(51, 255, 102)  # Teal
    ColorEmph = QColor(51, 255, 102)  # Green
    ColorActive = QColor(255, 102, 51)  # Orange

    ColorBorderBase = QColor('#e0e0e0')  # Whiteish
    ColorBorderActive = QColor(255, 222, 122)  # Yellowish

    MainTextFont = QFont('SansSerif', 12)
    SecondaryTextFont = QFont('SansSerif', 10)
    BodyTextFont = QFont('SansSerif', 8)

    NibTriangleHeight = 10.0
    NibTriangleWidth = 5.0

    LeftNibPainter = TrianglePainter(TriangleDrawOption_Horizontal.LeftApex)
    RightNibPainter = TrianglePainter(TriangleDrawOption_Horizontal.RightApex)

    def __init__(self, startTime=datetime.now(), endTime=None, name='', title='', subtitle='', color=QColor(51, 255, 102), extended_data=dict(), parent=None):
        super(PhoDurationEvent_AnnotationComment, self).__init__(startTime, endTime, name, color, extended_data, parent=parent)
        self.title = title
        self.subtitle = subtitle

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

        # Construct the nibs:
        halfNibOffset = (PhoDurationEvent_AnnotationComment.NibTriangleWidth / 2.0)

        # Offset the rect by the nibs
        body_y = (y+PhoDurationEvent_AnnotationComment.NibTriangleHeight)
        body_height = (height - PhoDurationEvent_AnnotationComment.NibTriangleHeight)
        bodyRect = QRect(x,body_y, width, body_height)

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)

        if self.is_deemphasized:
            activeColor = Qt.lightGray
        else:
            # de-emphasized overrides emphasized status
            if self.is_emphasized:
                activeColor = PhoDurationEvent_AnnotationComment.ColorEmph
            else:
                activeColor = self.color

        if self.is_active:
            painter.setPen(QtGui.QPen(PhoDurationEvent_AnnotationComment.ColorBorderActive, 4.0, join=Qt.MiterJoin))
            painter.setBrush(QBrush(PhoDurationEvent_AnnotationComment.ColorActive, Qt.SolidPattern))
        else:
            painter.setPen(QtGui.QPen(PhoDurationEvent_AnnotationComment.ColorBorderBase, 1.5, join=Qt.MiterJoin))
            painter.setBrush(QBrush(activeColor, Qt.SolidPattern))

        # Draw start triangle nib
        startPos = x
        start_poly = PhoDurationEvent_AnnotationComment.LeftNibPainter.get_poly(startPos, PhoDurationEvent_AnnotationComment.NibTriangleHeight, PhoDurationEvent_AnnotationComment.NibTriangleWidth)
        

        if self.endTime is None:
            # Instantaneous type event
            # painter.setPen(Qt.NoPen)
            if self.is_emphasized:
                penWidth = 1.0
            else:
                penWidth = 0.2

            ## NOTE: Apparently for events as small as the instantaneous events (with a width of 2) the "Brush" or "fill" doesn't matter, only the stroke does.
            painter.setPen(QtGui.QPen(activeColor, penWidth, join=Qt.MiterJoin))
            painter.drawRect(x, body_y, width, body_height)

            # Draw Nib:
            painter.drawPolygon(start_poly)
        else:
            # Normal duration event (like for videos)
            painter.drawRoundedRect(x, body_y, width, body_height, PhoDurationEvent_AnnotationComment.RectCornerRounding, PhoDurationEvent_AnnotationComment.RectCornerRounding)
            
            startPos = (x+width)-PhoDurationEvent_AnnotationComment.NibTriangleWidth
            end_poly = PhoDurationEvent_AnnotationComment.RightNibPainter.get_poly(startPos, PhoDurationEvent_AnnotationComment.NibTriangleHeight, PhoDurationEvent_AnnotationComment.NibTriangleWidth)
        
            # If it's not an instantaneous event, draw the label
            self.titleHeight = self.precompute_text_height(PhoDurationEvent_AnnotationComment.MainTextFont)
            self.titleLabelRect = QRect(x, body_y, width, self.titleHeight)
            self.subtitleHeight = self.precompute_text_height(PhoDurationEvent_AnnotationComment.SecondaryTextFont)
            self.subtitleLabelRect = QRect(x, (body_y+self.titleHeight), width, self.subtitleHeight)
            self.bodyTextLabelRect = QRect(x, self.subtitleLabelRect.bottom(), width, (bodyRect.height()-(self.titleHeight + self.subtitleHeight)))
            # PhoDurationEvent_AnnotationComment.BodyTextFont

            # painter.drawText(bodyRect, Qt.AlignTop|Qt.AlignHCenter, self.title)
            # painter.drawText(bodyRect, Qt.AlignHCenter|Qt.AlignCenter, self.subtitle)
            # painter.drawText(bodyRect, Qt.AlignBottom|Qt.AlignHCenter, self.name)

            painter.drawText(self.titleLabelRect, Qt.AlignCenter, self.title)
            painter.drawText(self.subtitleLabelRect, Qt.AlignCenter, self.subtitle)
            painter.drawText(self.bodyTextLabelRect, Qt.AlignCenter, self.name)

            # Draw Nibs:
            painter.drawPolygon(start_poly)
            painter.drawPolygon(end_poly)

        painter.restore()
        return eventRect

    ## GUI CLASS


