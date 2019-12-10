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

from numpy import load

from GUI.UI.TickedTimelineDrawingBaseWidget import TickProperties, TickedTimelineDrawingBaseWidget

__textColor__ = QColor(187, 187, 187)
__font__ = QFont('Decorative', 10)

class QTimeLine(TickedTimelineDrawingBaseWidget):

    def __init__(self, totalStartTime, totalEndTime, totalDuration, duration, parent=None):
        super(QTimeLine, self).__init__(totalStartTime, totalEndTime, totalDuration, duration, parent=parent)

        # Set variables
        self.textColor = __textColor__
        self.font = __font__

    #     self.initUI()
    #
    # def initUI(self):
    #     self.setGeometry(300, 300, self.length, 200)

    # Draw the date labels:
    def drawTextLabels(self, painter):
        w = 0
        # Draw time
        scale = self.getScale()

        textLabelWidth = 100.0
        halfTextLabelWidth = float(textLabelWidth) / 2.0

        # Major markers (day markers)
        for aStaticMarkerData in self.referenceManager.get_static_major_marker_data():
            item_x_offset = self.referenceManager.compute_x_offset_from_datetime(self.width(), aStaticMarkerData.time)
            painter.drawText(item_x_offset - halfTextLabelWidth, 0, textLabelWidth, 100, Qt.AlignHCenter, self.get_time_string(item_x_offset * scale))


    # Draw bottom horizontal baseline line
    def drawHorizontalBaseLine(self, painter):
        painter.setPen(QPen(self.activeColor, 5, Qt.SolidLine))
        painter.drawLine(0, 40, self.width(), 40)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setPen(self.textColor)
        qp.setFont(self.font)
        qp.setRenderHint(QPainter.Antialiasing)

        # Draw the date labels:
        self.drawTextLabels(qp)

        # Draw bottom horizontal baseline line
        self.drawHorizontalBaseLine(qp)

        self.draw_tick_lines(qp)
        self.draw_indicator_lines(qp)

        if self.pointerPos is not None:
            line = QLine(QPoint(self.pointerTimePos/self.getScale(), 40),
                         QPoint(self.pointerTimePos/self.getScale(), self.height()))
            poly = QPolygon([QPoint(self.pointerTimePos/self.getScale() - 10, 20),
                             QPoint(self.pointerTimePos/self.getScale() + 10, 20),
                             QPoint(self.pointerTimePos/self.getScale(), 40)])
        else:
            line = QLine(QPoint(0, 0), QPoint(0, self.height()))
            poly = QPolygon([QPoint(-10, 20), QPoint(10, 20), QPoint(0, 40)])

        
        # Clear clip path
        path = QPainterPath()
        path.addRect(self.rect().x(), self.rect().y(), self.rect().width(), self.rect().height())
        qp.setClipPath(path)

        # Draw pointer
        qp.setPen(self.activeColor)
        qp.setBrush(QBrush(self.activeColor))

        qp.drawPolygon(poly)
        qp.drawLine(line)

        if self.parent():
            self.parent().get_reference_manager().draw(qp, event.rect(), self.getScale())

        qp.end()

    # Mouse movement
    def mouseMoveEvent(self, e):
        # if mouse is being pressed, update pointer
        if self.clicking:
            x = e.pos().x()
            
        super().mouseMoveEvent(e)


    # Mouse pressed
    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        if e.button() == Qt.LeftButton:
            x = e.pos().x()
            self.update()
            
    # Mouse release
    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)


    # Set text color
    def setTextColor(self, color):
        self.textColor = color

    # Set Font
    def setTextFont(self, font):
        self.font = font
