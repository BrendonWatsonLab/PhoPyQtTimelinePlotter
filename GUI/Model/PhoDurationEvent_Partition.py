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

from GUI.Model.PhoDurationEvent import *
from app.BehaviorsList import BehaviorsManager



class PhoDurationEvent_Partition(PhoDurationEvent):
    InstantaneousEventDuration = timedelta(seconds=2)
    RectCornerRounding = 8
    ColorBase = QColor(51, 204, 255)  # Teal '#33ccff'
    ColorEmph = QColor(51, 255, 102)  # Green '#33ff66'
    ColorActive = QColor(255, 102, 51)  # Orange

    ColorBorderBase = QColor('#e0e0e0')  # Whiteish
    ColorBorderActive = QColor(255, 222, 122)  # Yellowish

    MainTextFont = QFont('SansSerif', 10)

    # This defines a signal called 'closed' that takes no arguments.
    on_edit = pyqtSignal()
    # on_edit = pyqtSignal(datetime, datetime, str, str, str)
    # on_edit = pyqtSignal(PhoDurationEvent_Partition)

    def __init__(self, startTime=datetime.now(), endTime=None, name='', subtitle='', body='', color=QColor(51, 204, 255), type_id=BehaviorsManager.UnknownType_ID, subtype_id=BehaviorsManager.UnknownSubtype_ID, extended_data=dict(), parent=None):
        super(PhoDurationEvent_Partition, self).__init__(startTime, endTime, name, color, extended_data, parent=parent)
        self.subtitle = subtitle
        self.body = body

        self.type_id = type_id
        self.subtype_id = subtype_id

        self.color = BehaviorsManager().get_subtype_color(self.subtype_id)

        # TODO: init gui

        # Debug pallete
        # p = self.palette()
        # p.setColor(QPalette.Background, Qt.blue)
        # self.setAutoFillBackground(True)
        # self.setPalette(p)

        # self.initUI()

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
        self.is_emphasized = False
        self.is_active = True

    def on_button_released(self, event):
        self.is_emphasized = False
        self.is_active = False
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

        # print('Partition paint is called: ', finalEventRect)

        return self.finalEventRect
        # return parent_modified_event_rect
        


    ## GUI CLASS


