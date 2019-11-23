# PhoEvent.py
# Contains the different shapes to draw and what they represent (instantaneous events, intervals, etc)
# https://www.e-education.psu.edu/geog489/node/2301
# https://wiki.python.org/moin/PyQt/Making%20non-clickable%20widgets%20clickable

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QMenu, QComboBox
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QFontMetrics, QPalette
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

from GUI.Model.Events.PhoDurationEvent import *
from app.BehaviorsList import BehaviorsManager

class PhoDurationEvent_Partition(PhoDurationEvent):
    InstantaneousEventDuration = timedelta(seconds=2)
    RectCornerRounding = 8
    # ColorBase = QColor(51, 204, 255)  # Teal '#33ccff'
    ColorBase = QColor(55, 55, 55, PhoEvent.DefaultOpacity)  # Grey
    ColorEmph = QColor(51, 255, 102, PhoEvent.DefaultOpacity)  # Green '#33ff66'
    ColorActive = QColor(255, 102, 51, PhoEvent.DefaultOpacity)  # Orange

    ColorBorderBase = QColor('#e0e0e0')  # Whiteish
    ColorBorderActive = QColor(255, 222, 122)  # Yellowish

    MainTextFont = QFont('SansSerif', 10)

    # This defines a signal called 'on_edit' that takes no arguments.
    on_edit = pyqtSignal()
    # on_edit = pyqtSignal(datetime, datetime, str, str, str)
    # on_edit = pyqtSignal(PhoDurationEvent_Partition)

    # def __init__(self, startTime=datetime.now(), endTime=None, name='', subtitle='', body='', color=QColor(55, 55, 55, PhoEvent.DefaultOpacity), type_id=BehaviorsManager.UnknownType_ID, subtype_id=BehaviorsManager.UnknownSubtype_ID, extended_data=dict(), parent=None):
    def __init__(self, startTime=datetime.now(), endTime=None, name='', subtitle='', body='', color=QColor(55, 55, 55, PhoEvent.DefaultOpacity), type_id=None, subtype_id=None, extended_data=dict(), parent=None):
        super(PhoDurationEvent_Partition, self).__init__(startTime, endTime, name, color, extended_data, parent=parent)
        self.subtitle = subtitle
        self.body = body

        self.type_id = type_id
        self.subtype_id = subtype_id


    def showMenu(self, pos):
        menu = QMenu()
        clear_action = menu.addAction("Modify Partition")
        action = menu.exec_(self.mapToGlobal(pos))
        # action = menu.exec_(self.mapToParent(pos))
        # action = menu.exec_(pos)
        if action == clear_action:
            print("Modify Partition action!")
            self.on_edit.emit()

    def onActivated(self, text):
        self.name = text

    def on_button_clicked(self, event):
        self.set_state_selected()

    def on_button_released(self, event):
        self.set_state_deselected()

        if event.button() == Qt.LeftButton:
            print("Left click")
        elif event.button() == Qt.RightButton:
            print("Right click")
            currPos = self.finalEventRect.topLeft()
            self.showMenu(currPos)
        elif event.button() == Qt.MiddleButton:
            print("Middle click")
        else:
            print("Unknown click event!")

    def on_key_pressed(self, event):
        gey = event.key()
        self.func = (None, None)
        print('PhoDurationEvent_Partition.on_key_pressed!')
        if gey == Qt.Key_M:
            print("PhoDurationEvent_Partition.on_key_pressed: Key 'm' pressed!")
            # currPos = self.rect()
            # currPos = self.frameGeometry()
            # self.showMenu(currPos.topLeft())
            # currPos = self.frameGeometry().topLeft()
            # currPos = QPoint(0,0)
            currPos = self.finalEventRect.topLeft()
            # currPos = QPoint(-100,0)
            self.showMenu(currPos)
            
        elif gey == Qt.Key_Right:
            print("PhoDurationEvent_Partition.on_key_pressed: Right key pressed!, call drawFundBlock()")
            # self.func = (self.drawFundBlock, {})
            self.mModified = True
        # elif gey == Qt.Key_5:
        #     print("#5 pressed, call drawNumber()")
        #     self.func = (self.drawNumber, {"notePoint": QPoint(100, 100)})
        #     self.mModified = True

     # Sets the painter's config based on the current object's state (active, emphasized, deemph, etc)
    def set_painter_config(self, aPainter):
        currFillColor = self.color

        currPenColor = PhoDurationEvent.ColorBorderBase
        currPenWidth = 1.0
        
        currActiveBrush = None
        currActivePen = None

        if self.is_deemphasized:
            currFillColor = self.color.darker(300) # setting to 300 returns a color that has one-third the brightness
        else:
            # de-emphasized overrides emphasized status
            if self.is_emphasized:
                currFillColor = self.color.lighter(110) # returns a color that's 20% brighter
            else:
                currFillColor = self.color

            currFillColor.setAlpha(PhoEvent.DefaultOpacity)
        
        # Override if active (selected)
        if self.is_active:
            currPenWidth = 4.0
            currPenColor = PhoDurationEvent.ColorBorderActive # For active events, override the pen color too
            currFillColor = self.color.lighter(130) # returns a color that's 20% brighter
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


    def paint(self, painter, totalStartTime, totalEndTime, totalDuration, totalParentCanvasRect):
        parent_modified_event_rect = super(PhoDurationEvent_Partition, self).paint(painter, totalStartTime, totalEndTime, totalDuration, totalParentCanvasRect)
        # "total*" refers to the parent frame in which this event is to be drawn
        # totalStartTime, totalEndTime, totalDuration, totalParentCanvasRect
        parentOffsetRect = self.compute_parent_offset_rect(totalStartTime, totalEndTime, totalDuration, totalParentCanvasRect.width(), totalParentCanvasRect.height())
        x = parentOffsetRect.x() + totalParentCanvasRect.x()
        y = parentOffsetRect.y() + totalParentCanvasRect.y()
        width = parentOffsetRect.width()
        height = parentOffsetRect.height()
        self.finalEventRect = QRect(x,y,width,height)
        return self.finalEventRect
        # return parent_modified_event_rect
        


    ## GUI CLASS


