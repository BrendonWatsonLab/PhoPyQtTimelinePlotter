#!/usr/bin/python3
# -*- coding: utf-8 -*-
import tempfile
from base64 import b64encode

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QPoint, QLine, QRect, QRectF, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPalette, QPen, QPolygon, QPainterPath, QPixmap
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea, QVBoxLayout
import sys
import os


__backgroudColor__ = QColor(60, 63, 65)

class TickProperties:
    """
    pen: QPen
    """
    def __init__(self, color, lineThickness=None, style=None):
        self.pen = QPen(color, lineThickness, style)
        # Qt.SolidLine

    def get_pen(self):
        return self.pen
        

class TickedTimelineDrawingBaseWidget(QWidget):

    hoverChanged = pyqtSignal(int)
    positionChanged = pyqtSignal(int)

    defaultActiveColor = Qt.darkCyan
    defaultNowColor = Qt.red

    # static lines
    staticTimeDelininationTickLineProperties = TickProperties(QColor(187, 187, 187), 0.6, Qt.SolidLine)

    # dynamic (moving) lines
    videoPlaybackLineProperties = TickProperties(Qt.red, 1.0, Qt.SolidLine)
    hoverLineProperties = TickProperties(Qt.cyan, 0.8, Qt.DashLine)


    def __init__(self, duration, length, parent=None):
        super(TickedTimelineDrawingBaseWidget, self).__init__(parent=parent)
        self.duration = duration
        self.length = length

        # Set variables
        self.backgroundColor = __backgroudColor__
        self.pos = None
        self.video_pos = None
        self.pointerPos = None
        self.pointerTimePos = None
        self.clicking = False  # Check if mouse left button is being pressed
        self.is_in = False  # check if user is in the widget
        self.activeColor = TickedTimelineDrawingBaseWidget.defaultActiveColor
        self.nowColor = TickedTimelineDrawingBaseWidget.defaultNowColor

        self.is_driven_externally = False

        self.setMouseTracking(True)  # Mouse events
        self.setAutoFillBackground(True)  # background

        # set background
        pal = QPalette()
        pal.setColor(QPalette.Background, self.backgroundColor)
        self.setPalette(pal)


    def draw_tick_lines(self, painter):
        # Draw dash lines
        point = 0
        painter.setPen(TickedTimelineDrawingBaseWidget.staticTimeDelininationTickLineProperties.get_pen())
        # draw a horizontal line
        painter.drawLine(0, 40, self.width(), 40)
        while point <= self.width():
            if point % 30 != 0:
                painter.drawLine(3 * point, 40, 3 * point, 30)
            else:
                painter.drawLine(3 * point, 40, 3 * point, 20)
            point += 10

    # Draws the tick marks and the indicator lines
    def draw_indicator_lines(self, painter):

        # Draw video playback indicator line
        if self.video_pos is not None:
            painter.setPen(TickedTimelineDrawingBaseWidget.videoPlaybackLineProperties.get_pen())
            painter.drawLine(self.video_pos.x(), 0, self.video_pos.x(), self.height())


        # Draw hover line
        if self.pos is not None:
            if (self.is_in or self.is_driven_externally): 
                painter.setPen(TickedTimelineDrawingBaseWidget.hoverLineProperties.get_pen())
                painter.drawLine(self.pos.x(), 0, self.pos.x(), self.height())



    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing)

        self.draw_tick_lines(qp)
        self.draw_indicator_lines(qp)

        # # Clear clip path
        # path = QPainterPath()
        # path.addRect(self.rect().x(), self.rect().y(), self.rect().width(), self.rect().height())
        # qp.setClipPath(path)

        qp.end()

    # Mouse movement
    def mouseMoveEvent(self, e):
        self.pos = e.pos()
        x = self.pos.x()

        self.hoverChanged.emit(x)

        # if mouse is being pressed, update pointer
        if self.clicking:
            self.pointerPos = x
            self.positionChanged.emit(x)
            self.pointerTimePos = self.pointerPos*self.getScale()

        self.update()

    # Mouse pressed
    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            x = e.pos().x()
            self.pointerPos = x
            self.positionChanged.emit(x)
            self.pointerTimePos = self.pointerPos * self.getScale()

            self.update()
            self.clicking = True  # Set clicking check to true

    # Mouse release
    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicking = False  # Set clicking check to false

    # Enter
    def enterEvent(self, e):
        self.is_in = True
        self.is_driven_externally = False

    # Leave
    def leaveEvent(self, e):
        self.is_in = False
        self.update()

    # Get time string from seconds
    def get_time_string(self, seconds):
        m, s = divmod(seconds, 60)
        h, m = divmod(m, 60)
        return "%02d:%02d:%02d" % (h, m, s)


    # Get scale from length
    def getScale(self):
        return float(self.duration)/float(self.width())

    # Get duration
    def getDuration(self):
        return self.duration

    # Set background color
    def setBackgroundColor(self, color):
        self.backgroundColor = color


    @pyqtSlot(int)
    def on_update_hover(self, x):
        self.is_driven_externally = True
        self.pos = QPoint(x, 0)
        self.update()


    @pyqtSlot(int)
    def on_update_video_line(self, x):
        # passing in None for x allows the line to be removed
        if x is None:
            self.video_pos = None
        else:
            self.video_pos = QPoint(x, 0)
        
        self.update()