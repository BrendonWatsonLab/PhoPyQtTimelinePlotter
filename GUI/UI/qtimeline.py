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

class VideoSample:

    def __init__(self, duration, color=Qt.darkYellow, picture=None, audio=None):
        self.duration = duration
        self.color = color  # Floating color
        self.defColor = color  # DefaultColor
        if picture is not None:
            self.picture = picture.scaledToHeight(45)
        else:
            self.picture = None
        self.startPos = 0  # Inicial position
        self.endPos = self.duration  # End position




class QTimeLine(TickedTimelineDrawingBaseWidget):

    def __init__(self, duration, length):
        super(QTimeLine, self).__init__(duration, length)

        # Set variables
        self.textColor = __textColor__
        self.font = __font__
        self.selectedSample = None
        self.videoSamples = []  # List of videos samples

        self.initUI()

    def initUI(self):
        self.setGeometry(300, 300, self.length, 200)


    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setPen(self.textColor)
        qp.setFont(self.font)
        qp.setRenderHint(QPainter.Antialiasing)
        w = 0
        # Draw time
        scale = self.getScale()
        while w <= self.width():
            qp.drawText(w - 50, 0, 100, 100, Qt.AlignHCenter, self.get_time_string(w * scale))
            w += 100

        # Draw bottom horizontal baseline line
        qp.setPen(QPen(self.activeColor, 5, Qt.SolidLine))
        qp.drawLine(0, 40, self.width(), 40)

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

        # Draw samples
        t = 0
        for sample in self.videoSamples:
            # Clear clip path
            path = QPainterPath()
            path.addRoundedRect(QRectF(t / scale, 50, sample.duration / scale, 200), 10, 10)
            qp.setClipPath(path)

            # Draw sample
            path = QPainterPath()
            qp.setPen(sample.color)
            path.addRoundedRect(QRectF(t/scale, 50, sample.duration/scale, 50), 10, 10)
            sample.startPos = t/scale
            sample.endPos = t/scale + sample.duration/scale
            qp.fillPath(path, sample.color)
            qp.drawPath(path)

            # Draw preview pictures
            if sample.picture is not None:
                if sample.picture.size().width() < sample.duration/scale:
                    path = QPainterPath()
                    path.addRoundedRect(QRectF(t/scale, 52.5, sample.picture.size().width(), 45), 10, 10)
                    qp.setClipPath(path)
                    qp.drawPixmap(QRect(t/scale, 52.5, sample.picture.size().width(), 45), sample.picture)
                else:
                    path = QPainterPath()
                    path.addRoundedRect(QRectF(t / scale, 52.5, sample.duration/scale, 45), 10, 10)
                    qp.setClipPath(path)
                    pic = sample.picture.copy(0, 0, sample.duration/scale, 45)
                    qp.drawPixmap(QRect(t / scale, 52.5, sample.duration/scale, 45), pic)
            t += sample.duration

        # Clear clip path
        path = QPainterPath()
        path.addRect(self.rect().x(), self.rect().y(), self.rect().width(), self.rect().height())
        qp.setClipPath(path)

        # Draw pointer
        qp.setPen(self.activeColor)
        qp.setBrush(QBrush(self.activeColor))

        qp.drawPolygon(poly)
        qp.drawLine(line)

        print("paintEvent({0})".format(str(event)))
        curr_pos = QPoint((float(self.width()) * 0.10), 0.0)
        self.referenceManager.get_markers()["0"].update_position(curr_pos, self.getScale())

        curr_pos = QPoint((float(self.width()) * 0.20), 0.0)
        self.referenceManager.get_markers()["1"].update_position(curr_pos, self.getScale())

        curr_pos = QPoint((float(self.width()) * 0.30), 0.0)
        self.referenceManager.get_markers()["2"].update_position(curr_pos, self.getScale())

        self.referenceManager.draw(qp, event.rect(), self.getScale())


        qp.end()

    # Mouse movement
    def mouseMoveEvent(self, e):
        # if mouse is being pressed, update pointer
        if self.clicking:
            x = e.pos().x()
            self.checkSelection(x)

        super().mouseMoveEvent(e)


    # Mouse pressed
    def mousePressEvent(self, e):
        super().mousePressEvent(e)
        if e.button() == Qt.LeftButton:
            x = e.pos().x()
            self.checkSelection(x)
            self.update()
            
    # Mouse release
    def mouseReleaseEvent(self, e):
        super().mouseReleaseEvent(e)

    # check selection
    def checkSelection(self, x):
        # Check if user clicked in video sample
        for sample in self.videoSamples:
            if sample.startPos < x < sample.endPos:
                sample.color = self.activeColor
                if self.selectedSample is not sample:
                    self.selectedSample = sample
                    self.selectionChanged.emit(sample)
            else:
                sample.color = sample.defColor

    # Get selected sample
    def getSelectedSample(self):
        return self.selectedSample

    # Set text color
    def setTextColor(self, color):
        self.textColor = color

    # Set Font
    def setTextFont(self, font):
        self.font = font
