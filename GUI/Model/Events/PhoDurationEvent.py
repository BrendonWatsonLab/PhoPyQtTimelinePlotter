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

from GUI.Model.Events.PhoEvent import *
from GUI.UI.EdgeAndCornerSelectionViewHelpers import EdgeAndCornerContainerComponent, EdgeAndCornerContainerViewMixin

class PhoDurationEvent(EdgeAndCornerContainerViewMixin, PhoEvent):
    InstantaneousEventDuration = timedelta(seconds=2)
    RectCornerRounding = 8
    ColorBase = QColor(51, 204, 255, PhoEvent.DefaultOpacity)  # Teal
    ColorEmph = QColor(51, 255, 102, PhoEvent.ActiveOpacity)  # Green
    ColorActive = QColor(255, 102, 51, PhoEvent.ActiveOpacity)  # Orange

    ColorBorderBase = QColor('#e0e0e0')  # Whiteish
    ColorBorderActive = QColor(255, 222, 122)  # Yellowish

    MainTextFont = QFont('SansSerif', 10)

    def __init__(self, startTime=datetime.now(), endTime=None, name='', color=QColor(51, 204, 255, PhoEvent.DefaultOpacity), extended_data=dict(), parent=None):
        super(PhoDurationEvent, self).__init__(startTime, name, color, extended_data, parent=parent)
        self.endTime = endTime
        self.init_EdgeAndCornerContainerViewMixin()

    def __eq__(self, otherEvent):
        return self.name == otherEvent.name and self.startTime == otherEvent.startTime and self.endTime == otherEvent.endTime

    # Less Than (<) operator
    def is_entirely_less_than(self, otherEvent):
        # Returns true if this event is entirely less than the otherEvent (meaning it both starts AND completes before the start of the otherEvent)
        return self.startTime < otherEvent.startTime and self.endTime < otherEvent.startTime

    def is_entirely_greater_than(self, otherEvent):
        # Returns true if this event is entirely greater than the otherEvent (meaning it both starts AND completes after the end of the otherEvent)
        return self.startTime > otherEvent.endTime and self.endTime > otherEvent.endTime

    # returns true if this is an instantaneous event (meaning it doesn't have an endTime)
    def is_instantaneous_event(self):
        return (self.endTime is None)

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

    # returns true if the absolute_datetime falls within the event. Always false for an instantaneous event
    def contains(self, absolute_datetime):
        if (self.is_instantaneous_event()):
            return False
        else:
            return ((self.startTime <= absolute_datetime) and (self.endTime >= absolute_datetime))

    def precompute_text_height(self, font):
        qm = QFontMetrics(font)
        return qm.height()

    def precompute_text_width(self, font, text):
        qm = QFontMetrics(font)
        return qm.width(text)

    def __str__(self):
        return 'Event {0}: [startTime: {1}, endTime: {2}], duration: {3}, extended_data: {4}'.format(self.name, self.startTime, self.endTime, self.computeDuration(), str(self.extended_data))

    def computeDuration(self):
        if self.endTime:
            return (self.endTime - self.startTime)
        else:
            return PhoDurationEvent.InstantaneousEventDuration

    def buildMenu(self):
        self.menu = QMenu()
        self.info_action = self.menu.addAction("Get Info")
        sep1 = self.menu.addSeparator()
        self.createMarkerAtStart = self.menu.addAction("Marker at Start")
        self.createMarkerAtEnd = self.menu.addAction("Marker at End")
        sep2 = self.menu.addSeparator()
        self.modify_action = self.menu.addAction("Modify...")
        self.delete_action = self.menu.addAction("Delete...")
        return self.menu

    # handleMenuAction(action): returns None if the action was resolved, or the action if it wasn't
    def handleMenuAction(self, action):
        if action == self.info_action:
            print("PhoDurationEvent.Get Info action!")
            self.on_info.emit(self.get_track_index())
        elif action == self.modify_action:
            print("PhoDurationEvent.Modify action!")
            self.on_edit.emit(self.get_track_index())
        elif action == self.delete_action:
            print("PhoDurationEvent.Delete action!")
            self.on_delete.emit(self.get_track_index())

        elif action == self.createMarkerAtStart:
            print("PhoDurationEvent.createMarkerAtStart action!")
            self.on_create_marker_at_start.emit(self.get_track_index(), self.startTime)
        elif action == self.createMarkerAtEnd:
            print("PhoDurationEvent.createMarkerAtEnd action!")
            self.on_create_marker_at_end.emit(self.get_track_index(), self.endTime)
        else:
            print("Unknown menu option! for track {0}".format(str(self.get_track_index())))
            return action
        
        return None

    # showMenu(pos): should NOT be overriden! Override buildMenu(...) and handleMenuAction(...) instead
    def showMenu(self, pos):
        print("PhoDurationEvent.showMenu(pos: {0})".format(str(pos)))
        menu = self.buildMenu()
        action = menu.exec_(self.mapToGlobal(pos))
        self.handleMenuAction(action)


    def on_button_clicked(self, event):
        self.set_state_selected()

    def on_button_released(self, event):
        self.set_state_deselected()
        if event.button() == Qt.LeftButton:
            print("PhoDurationEvent.on_button_released(...): Left click")
        elif event.button() == Qt.RightButton:
            print("PhoDurationEvent.on_button_released(...): Right click")
            currPos = self.finalEventRect.topLeft()
            self.showMenu(currPos)
        elif event.button() == Qt.MiddleButton:
            print("PhoDurationEvent.on_button_released(...): Middle click")
        else:
            print("PhoDurationEvent.on_button_released(...): Unknown click event!")

    def on_key_pressed(self, event):
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

    # Returns the absolute (wall/world) time for a relative_duration into the event)
    def compute_absolute_time(self, relative_duration):
        return (self.startTime + relative_duration)

    def compute_parent_offset_rect(self, totalStartTime, totalEndTime, totalDuration, totalParentWidth, totalParentHeight):
        # "total*" refers to the parent frame in which this event is to be drawn
        # totalStartTime, totalEndTime, totalDuration, totalParentCanvasRect
        percentDuration = (self.computeDuration() / totalDuration)
        offsetStartDuration = self.startTime - totalStartTime
        percentOffsetStart = offsetStartDuration / totalDuration
        x = percentOffsetStart * totalParentWidth
        width = percentDuration * totalParentWidth
        height = totalParentHeight
        y = 0.0
        return QRect(x, y, width, height)


    # overrides:
    def set_state_selected(self):
        super().set_state_selected()

    def set_state_deselected(self):
        super().set_state_deselected()
        self.clearSelected_EdgeAndCornerContainerViewMixin()
        
    def set_state_emphasized(self):
        super().set_state_emphasized()

    def set_state_deemphasized(self):
        super().set_state_deemphasized()
        self.clearHovered_EdgeAndCornerContainerViewMixin()


    # Sets the painter's config based on the current object's state (active, emphasized, deemph, etc)
    def set_painter_config(self, aPainter):
        currFillColor = self.color

        currPenColor = PhoDurationEvent.ColorBorderBase
        currPenWidth = 1.0
        
        currActiveBrush = None
        currActivePen = None

        if self.is_deemphasized:
            currFillColor = Qt.lightGray
            currFillColor.setAlpha(PhoEvent.DeEmphOpacity)
        else:
            # de-emphasized overrides emphasized status
            if self.is_emphasized:
                currFillColor = PhoDurationEvent.ColorEmph
            else:
                currFillColor = self.color

            currFillColor.setAlpha(PhoEvent.DefaultOpacity)
            

        # Override if active (selected)
        if self.is_active:
            currPenWidth = 4.0
            currPenColor = PhoDurationEvent.ColorBorderActive # For active events, override the pen color too
            currFillColor = PhoDurationEvent.ColorActive # For active events, override the color with the current active color
            currFillColor.setAlpha(PhoEvent.ActiveOpacity)

        else:
            currPenWidth = 1.5
            currPenColor = PhoDurationEvent.ColorBorderBase
            
            
        # Instantaneous type event: for instantaneous events, we must render them in their characteristic color (which is the fill color) with a fixed width so they can be visible and recognized
        if self.is_instantaneous_event():
            
            # painter.setPen(Qt.NoPen)
            if self.is_emphasized:
                currPenWidth = 1.0
            else:
                currPenWidth = 0.2

            ## NOTE: Apparently for events as small as the instantaneous events (with a width of 2) the "Brush" or "fill" doesn't matter, only the stroke does.
            # we must render them in their characteristic color (which is the fill color)
            currPenColor = currFillColor

        currActivePen = QtGui.QPen(currPenColor, currPenWidth, join=Qt.MiterJoin)
        currActiveBrush = QBrush(currFillColor, Qt.SolidPattern)

        aPainter.setPen(currActivePen)
        aPainter.setBrush(currActiveBrush)
        return


    # "pass": specifies that we're leaving this method "virtual" or intensionally empty to be overriden by a subclass.
    def paint(self, painter, totalStartTime, totalEndTime, totalDuration, totalParentCanvasRect):
        parentOffsetRect = self.compute_parent_offset_rect(totalStartTime, totalEndTime, totalDuration, totalParentCanvasRect.width(), totalParentCanvasRect.height())
        x = parentOffsetRect.x() + totalParentCanvasRect.x()
        y = parentOffsetRect.y() + totalParentCanvasRect.y()
        width = parentOffsetRect.width()
        height = parentOffsetRect.height()

        self.finalEventRect = QRect(x,y,width,height)
        # painter.setPen( QtGui.QPen( Qt.darkBlue, 2, join=Qt.MiterJoin ) )

        painter.save()
        painter.setRenderHint(QPainter.Antialiasing)
        self.set_painter_config(painter)

        if self.is_instantaneous_event():
            # ## NOTE: Apparently for events as small as the instantaneous events (with a width of 2) the "Brush" or "fill" doesn't matter, only the stroke does.
            painter.drawRect(x, y, width, height)
        else:
            # Normal duration event (like for videos)
            painter.drawRoundedRect(x, y, width, height, PhoDurationEvent.RectCornerRounding, PhoDurationEvent.RectCornerRounding)
            # If it's not an instantaneous event, draw the label
            painter.drawText(self.finalEventRect, Qt.AlignCenter, self.name)

        self.paintEvent_EdgeAndCornerContainerViewMixin(painter, self.finalEventRect)
        
        painter.restore()
        return self.finalEventRect

    ## GUI CLASS


