#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ReferenceLineManager.py
import sys
from datetime import datetime, timezone, timedelta
import queue
import numpy as np

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QPoint, QLine, QRect, QRectF, pyqtSignal, pyqtSlot, QObject, QMargins
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPalette, QPen, QPolygon, QPainterPath, QPixmap
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea, QVBoxLayout, QGridLayout, QListWidget
import os

from GUI.UI.ReferenceMarkViewer.ReferenceMarkViewer import ReferenceMarkViewer, ActiveReferenceMarkersMixin

## IMPORTS:
# from GUI.Model.ReferenceLines.ReferenceMarkerVisualHelpers import TickProperties, ReferenceMarker

__textColor__ = QColor(20, 20, 20)
__font__ = QFont('Decorative', 12)


class TickProperties:
    """
    pen: QPen
    """
    def __init__(self, color, lineThickness=None, style=None):
        self.pen = QPen(color, lineThickness, style)

    def get_pen(self):
        return self.pen

    def get_color(self):
        return self.get_pen().color()


"""
ReferenceMarker: a QObject that draws a vertical line that denotes a specific timestamp on a timeline with an optional triangular header with a ID Label
"""
class ReferenceMarker(QObject):

    defaultProperties = TickProperties(QColor(250, 187, 187), 0.9, Qt.SolidLine)
    
    def __init__(self, identifier, is_enabled, properties=TickProperties(QColor(250, 187, 187), 0.9, Qt.SolidLine), parent=None):
        super().__init__(parent=parent)
        self.identifier = identifier
        self.is_enabled = is_enabled
        self.properties = properties
        self.scale = 1.0
        self.x_offset_position = None
        self.textColor = __textColor__
        self.font = __font__

        self.drawsPointer = True
        self.drawsText = True

        self.is_driven_externally = False

    def draw_pointer(self, painter, drawRect, scale):
        if self.x_offset_position is not None:
            currOffset = (self.get_pointerTimePos()/scale)
            line = QLine(QPoint(currOffset, 40),
                         QPoint(currOffset, drawRect.height()))
            poly = QPolygon([QPoint(currOffset - 10, 20),
                             QPoint(currOffset + 10, 20),
                             QPoint(currOffset, 40)])

            
        else:
            line = QLine(QPoint(0, 0), QPoint(0, self.height()))
            poly = QPolygon([QPoint(-10, 20), QPoint(10, 20), QPoint(0, 40)])

        # Draw pointer
        painter.setPen(self.properties.get_pen())
        painter.setBrush(QBrush(self.properties.get_color()))

        painter.drawPolygon(poly)
        painter.drawLine(line)

        if self.drawsText:
            # Draw text
            painter.setPen(self.textColor)
            painter.setFont(self.font)
            textRect = poly.boundingRect()
            textRect = textRect.marginsRemoved(QMargins(0, 0, 0, 4))

            painter.drawText(textRect, Qt.AlignCenter, self.identifier)



    # Called to draw the line and optionally the triangular pointer
    def draw(self, painter, drawRect, scale):
        self.updateScale(scale)
        if self.is_enabled:
            if self.x_offset_position is not None:
                painter.setRenderHint(QPainter.Antialiasing)

                # Draws the single vertical line across the entire height of the drawRect
                painter.setPen(self.properties.get_pen())
                painter.drawLine(self.x_offset_position, 0, self.x_offset_position, drawRect.height())

                if (self.drawsPointer):
                    self.draw_pointer(painter, drawRect, scale)

    def getScale(self):
        return self.scale

    def get_x_offset_position(self):
        return self.x_offset_position

    def get_pointerTimePos(self):
        return (self.x_offset_position * self.getScale())

    def updateScale(self, newScale):
        if (self.scale != newScale):
            self.scale = newScale

    # Updates the position and scale of the reference marker
    def update_position(self, x_offset_position, scale):
        self.x_offset_position = x_offset_position
        self.updateScale(scale)

    def get_position_tuple_string(self):
        return '(pos: {0}, get_pointerTimePos: {1})'.format(self.x_offset_position, self.get_pointerTimePos())

    def __str__(self):
        return 'RefMark[identifier: {0}]: {1}'.format(self.identifier, self.get_position_tuple_string())

    def get_is_enabled(self):
        return self.is_enabled

    def updateIsEnabled(self, newIsEnabled):
        self.is_enabled = newIsEnabled