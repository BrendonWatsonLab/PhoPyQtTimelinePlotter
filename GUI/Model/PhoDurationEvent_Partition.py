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

class PhoDurationEvent_Partition(PhoDurationEvent):
    InstantaneousEventDuration = timedelta(seconds=2)
    RectCornerRounding = 8
    ColorBase = QColor(51, 204, 255)  # Teal '#33ccff'
    ColorEmph = QColor(51, 255, 102)  # Green '#33ff66'
    ColorActive = QColor(255, 102, 51)  # Orange

    ColorBorderBase = QColor('#e0e0e0')  # Whiteish
    ColorBorderActive = QColor(255, 222, 122)  # Yellowish

    MainTextFont = QFont('SansSerif', 10)

    def __init__(self, startTime=datetime.now(), endTime=None, name='', color=QColor(51, 204, 255), extended_data=dict(), parent=None):
        super(PhoDurationEvent_Partition, self).__init__(startTime, endTime, name, color, extended_data, parent=parent)
        # TODO: init gui

        # Debug pallete
        # p = self.palette()
        # p.setColor(QPalette.Background, Qt.blue)
        # self.setAutoFillBackground(True)
        # self.setPalette(p)

        # self.initUI()

    # def initUI(self):
    #     # QtWidgets.QWidget()
    #     minimumWidgetWidth = 10
    #     self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        
    #     self.frameWidget = QFrame(self)
    #     self.frameWidget.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Expanding)
    #     # self.frameWidget.setMinimumSize(minimumWidgetWidth, 50)
    #     self.frameWidget.setAutoFillBackground(True)
    #     self.frameWidget.setMouseTracking(True)
    #     # self.frameWidget.setStyleSheet("background-color: red; border: 1px solid black; border-radius: 8px")
    #     self.frameWidget.setStyleSheet("background-color: #33ccff; border: 1px solid #e0e0e0; border-radius: 8px")

    #     self.lblTitle = QLabel("Title",self)
    #     self.lblTitle.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

    #     self.lblSubtitle = QLabel("Subtitle",self)
    #     self.lblSubtitle.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

    #     self.comboBox = QComboBox(self)
    #     self.comboBox.customContextMenuRequested.connect(self.showMenu)
    #     self.comboBox.addItem("Ubuntu")
    #     self.comboBox.addItem("Mandriva")
    #     self.comboBox.addItem("Fedora")
    #     self.comboBox.addItem("Red Hat")
    #     self.comboBox.addItem("Gentoo")
    #     self.comboBox.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)

    #      #Layout of Extended Tracks Container Widget
    #     self.mainVboxLayout = QVBoxLayout(self)
    #     self.mainVboxLayout.addStretch(1)
    #     self.mainVboxLayout.addSpacing(0.2)
    #     self.mainVboxLayout.setContentsMargins(0, 0, 0, 0)

    #     self.mainVboxLayout.addWidget(self.lblTitle)
    #     # self.lblTitle.setMinimumSize(minimumWidgetWidth, 10)

    #     self.mainVboxLayout.addWidget(self.lblSubtitle)
    #     # self.lblSubtitle.setMinimumSize(minimumWidgetWidth, 10)

    #     self.mainVboxLayout.addWidget(self.comboBox)
    #     # self.comboBox.setMinimumSize(minimumWidgetWidth, 10)

    #     self.frameWidget.setLayout(self.mainVboxLayout)

    #     # self.comboBox.move(0, 0)
    #     # self.lbl.move(50, 150)

    #     self.comboBox.activated[str].connect(self.onActivated)

    #     self.rootVboxLayout = QVBoxLayout(self)
    #     self.rootVboxLayout.addWidget(self.frameWidget)
    #     self.rootVboxLayout.setContentsMargins(0, 0, 0, 0)
    #     self.setLayout(self.rootVboxLayout)

    #     # self.setGeometry(300, 300, 300, 200)

    def showMenu(self, pos):
        menu = QMenu()
        clear_action = menu.addAction("Clear Selection")
        action = menu.exec_(self.mapToGlobal(pos))
        # action = menu.exec_(self.mapToParent(pos))
        # action = menu.exec_(pos)
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

        # self.resize(width, height)
        # self.frameWidget.resize(width, height)
        # self.frameWidget.move(x, y)

        # self.setGeometry(finalEventRect)
        # self.setMaximumWidth(width)

        # self.setGeometry(x, y, width, height)
        # self.updateGeometry()

        # self.frameWidget.setMaximumWidth(width)
        # self.frameWidget.setFixedWidth(width)

        # self.update()

        # self.move(x, y)
        # self.setFixedWidth(width)

        # self.move(x, y)
        
        # self.setGeometry(finalEventRect)     
        # self.frameWidget.setMinimumSize(width, 50)
        # self.frameWidget.setFixedWidth(width)
        # self.updateGeometry()
        # self.update()

        # self.widget.move(self.width() - self.widget.width() - 1, 1)

        # self.comboBox.paint
        
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
        return self.finalEventRect
        # return parent_modified_event_rect
        


    ## GUI CLASS


