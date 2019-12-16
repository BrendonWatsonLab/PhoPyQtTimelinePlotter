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
__font__ = QFont('Decorative', 11)
__minor_font__ = QFont('Decorative', 8)

class QTimeLine(TickedTimelineDrawingBaseWidget):

    def __init__(self, totalStartTime, totalEndTime, totalDuration, duration, parent=None):
        super(QTimeLine, self).__init__(totalStartTime, totalEndTime, totalDuration, duration, parent=parent)

        # Set variables


        # Text Label Options:
        self.textColor = __textColor__
        self.font = __font__
        self.minor_font = __minor_font__

        self.textLabelWidth = 100.0
        self.halfTextLabelWidth = float(self.textLabelWidth) / 2.0

        self.majorTextVerticalOffset = 0.0
        self.minorTextVerticalOffset = 10.0


        self.indicatorTextVerticalOffset_Hover = 0.0
        self.indicatorTextVerticalOffset_VideoPlayback = 0.0
        

    # Draw the date labels:
    def drawTextLabels(self, painter):

        # Major markers (day markers)
        painter.setPen(self.textColor)
        painter.setFont(self.font)
        for aStaticMarkerData in self.referenceManager.get_static_major_marker_data():
            item_x_offset = self.referenceManager.compute_x_offset_from_datetime(self.width(), aStaticMarkerData.time)
            painter.drawText(item_x_offset - self.halfTextLabelWidth, self.majorTextVerticalOffset, self.textLabelWidth, 100, Qt.AlignHCenter, self.get_start_of_day_time_string(aStaticMarkerData.time))

        # Minor markers (hour markers)
        painter.setFont(self.minor_font)
        for aStaticMarkerData in self.referenceManager.get_static_minor_marker_data():
            item_x_offset = self.referenceManager.compute_x_offset_from_datetime(self.width(), aStaticMarkerData.time)
            painter.drawText(item_x_offset - self.halfTextLabelWidth, self.minorTextVerticalOffset, self.textLabelWidth, 100, Qt.AlignHCenter, self.get_hours_of_day_only_time_string(aStaticMarkerData.time))


    # Draws the current hover and video playback time *text labels*
    def drawCurrentIndicatorTextLabels(self, painter):
        painter.setFont(self.font)

        # Draw video playback indicator line
        # videoPlaybackIndicatorMarkerContainer = self.referenceManager.get_indicator_marker_video_playback()
        # # Update hover line visibility
        # hoverIndicatorMarkerContainer = self.referenceManager.get_indicator_marker_user_hover()

        # Draw video playback indicator line
        if self.video_pos is not None:
            painter.setPen(TickedTimelineDrawingBaseWidget.videoPlaybackLineProperties.get_pen())
            # painter.drawLine(self.video_pos.x(), 0, self.video_pos.x(), self.height())
            videoPlaybackIndicatorMarkerContainer = self.referenceManager.get_indicator_marker_video_playback()
            

            
            painter.drawText(self.video_pos.x() - self.halfTextLabelWidth, self.indicatorTextVerticalOffset_VideoPlayback, self.textLabelWidth, 100, Qt.AlignHCenter, self.get_full_long_date_time_twoLine_string(videoPlaybackIndicatorMarkerContainer.get_record().time))



        # Draw hover line
        if self.pos is not None:
            if (self.is_in or self.is_driven_externally): 
                painter.setPen(TickedTimelineDrawingBaseWidget.hoverLineProperties.get_pen())
                # painter.drawLine(self.pos.x(), 0, self.pos.x(), self.height())
                hoverIndicatorMarkerContainer = self.referenceManager.get_indicator_marker_user_hover()
                painter.drawText(self.pos.x() - self.halfTextLabelWidth, self.indicatorTextVerticalOffset_Hover, self.textLabelWidth, 100, Qt.AlignHCenter, self.get_full_long_date_time_twoLine_string(hoverIndicatorMarkerContainer.get_record().time))


        pass


    # Draw bottom horizontal baseline line
    def drawHorizontalBaseLine(self, painter):
        painter.setPen(QPen(self.activeColor, 5, Qt.SolidLine))
        painter.drawLine(0, 40, self.width(), 40)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing)

        # Draw the static date labels:
        self.drawTextLabels(qp)

        # Draw the dynamic indicator labels
        self.drawCurrentIndicatorTextLabels(qp)

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
