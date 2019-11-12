# PhoEvent.py
# Contains the different shapes to draw and what they represent (instantaneous events, intervals, etc)
# https://www.e-education.psu.edu/geog489/node/2301
# https://wiki.python.org/moin/PyQt/Making%20non-clickable%20widgets%20clickable

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QMenu, QComboBox
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QFontMetrics
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

from GUI.Model.PhoDurationEvent import *

class PhoDurationEvent_Partition(PhoDurationEvent):
    InstantaneousEventDuration = timedelta(seconds=2)
    RectCornerRounding = 8
    ColorBase = QColor(51, 204, 255)  # Teal
    ColorEmph = QColor(51, 255, 102)  # Green
    ColorActive = QColor(255, 102, 51)  # Orange

    ColorBorderBase = QColor('#e0e0e0')  # Whiteish
    ColorBorderActive = QColor(255, 222, 122)  # Yellowish

    MainTextFont = QFont('SansSerif', 10)

    def __init__(self, startTime=datetime.now(), endTime=None, name='', color=QColor(51, 204, 255), extended_data=dict()):
        super(PhoDurationEvent_Partition, self).__init__(startTime, endTime, name, color, extended_data)
        # TODO: init gui
        self.initUI()

    def initUI(self):
        self.comboBox = QComboBox()
        self.comboBox.customContextMenuRequested.connect(self.showMenu)
        self.comboBox.addItem("Ubuntu")
        self.comboBox.addItem("Mandriva")
        self.comboBox.addItem("Fedora")
        self.comboBox.addItem("Red Hat")
        self.comboBox.addItem("Gentoo")
        self.comboBox.move(0, 0)

        self.comboBox.activated[str].connect(self.onActivated)

    def showMenu(self,pos):
        menu = QMenu()
        clear_action = menu.addAction("Clear Selection")
        action = menu.exec_(self.mapToGlobal(pos))
        if action == clear_action:
            self.comboBox.setCurrentIndex(0)

    def onActivated(self, text):
        self.name = text

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

    def paint(self, painter, totalStartTime, totalEndTime, totalDuration, totalParentCanvasRect):
        parent_modified_event_rect = super(PhoDurationEvent_Partition, self).paint(painter, totalStartTime, totalEndTime, totalDuration, totalParentCanvasRect)
        # # "total*" refers to the parent frame in which this event is to be drawn
        # # totalStartTime, totalEndTime, totalDuration, totalParentCanvasRect
        # percentDuration = (self.computeDuration() / totalDuration)
        # offsetStartDuration = self.startTime - totalStartTime
        # percentOffsetStart = offsetStartDuration / totalDuration
        # x = percentOffsetStart * totalParentCanvasRect.width()
        # width = percentDuration * totalParentCanvasRect.width()
        # height = totalParentCanvasRect.height()
        # y = 0.0
        # eventRect = QRect(x, y, width, height)
        # # painter.setPen( QtGui.QPen( Qt.darkBlue, 2, join=Qt.MiterJoin ) )

        # painter.save()
        # painter.setRenderHint(QPainter.Antialiasing)

        # if self.is_deemphasized:
        #     activeColor = Qt.lightGray
        # else:
        #     # de-emphasized overrides emphasized status
        #     if self.is_emphasized:
        #         activeColor = PhoDurationEvent.ColorEmph
        #     else:
        #         activeColor = self.color

        # if self.is_active:
        #     painter.setPen(QtGui.QPen(PhoDurationEvent.ColorBorderActive, 4.0, join=Qt.MiterJoin))
        #     painter.setBrush(QBrush(PhoDurationEvent.ColorActive, Qt.SolidPattern))
        # else:
        #     painter.setPen(QtGui.QPen(PhoDurationEvent.ColorBorderBase, 1.5, join=Qt.MiterJoin))
        #     painter.setBrush(QBrush(activeColor, Qt.SolidPattern))

        # if self.endTime is None:
        #     # Instantaneous type event
        #     # painter.setPen(Qt.NoPen)
        #     if self.is_emphasized:
        #         penWidth = 1.0
        #     else:
        #         penWidth = 0.2

        #     ## NOTE: Apparently for events as small as the instantaneous events (with a width of 2) the "Brush" or "fill" doesn't matter, only the stroke does.
        #     painter.setPen(QtGui.QPen(activeColor, penWidth, join=Qt.MiterJoin))
        #     painter.drawRect(x, y, width, height)
        # else:
        #     # Normal duration event (like for videos)
        #     painter.drawRoundedRect(x, y, width, height, PhoDurationEvent.RectCornerRounding, PhoDurationEvent.RectCornerRounding)
        #     # If it's not an instantaneous event, draw the label
        #     painter.drawText(eventRect, Qt.AlignCenter, self.name)

        # painter.restore()
        # return eventRect
        return parent_modified_event_rect
    ## GUI CLASS


