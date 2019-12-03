#!/usr/bin/python3
# -*- coding: utf-8 -*-
import tempfile
from base64 import b64encode

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QPoint, QLine, QRect, QRectF, pyqtSignal, pyqtSlot, QObject, QMargins
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPalette, QPen, QPolygon, QPainterPath, QPixmap
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea, QVBoxLayout
import sys
import os


__backgroudColor__ = QColor(60, 63, 65)
# __textColor__ = QColor(187, 187, 187)
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


class ReferenceMarker(QObject):

    defaultProperties = TickProperties(QColor(250, 187, 187), 0.9, Qt.SolidLine)
    
    def __init__(self, identifier, is_enabled, properties=TickProperties(QColor(250, 187, 187), 0.9, Qt.SolidLine), parent=None):
        super().__init__(parent=parent)
        self.identifier = identifier
        self.is_enabled = is_enabled
        self.properties = properties
        self.scale = 1.0
        self.pos = None
        self.pointerPos = None
        self.textColor = __textColor__
        self.font = __font__

        self.is_driven_externally = False

    def draw_pointer(self, painter, drawRect, scale):
        if self.pointerPos is not None:
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

        # Draw text
        painter.setPen(self.textColor)
        painter.setFont(self.font)
        textRect = poly.boundingRect()
        textRect = textRect.marginsRemoved(QMargins(0, 0, 0, 4))

        # painter.drawText(currOffset - 10, 0, 20, 20, Qt.AlignHCenter, self.identifier)
        # painter.drawText(currOffset - 10, 20, 20, 20, Qt.AlignCenter, self.identifier)
        painter.drawText(textRect, Qt.AlignCenter, self.identifier)


    def draw(self, painter, drawRect, scale):
        self.updateScale(scale)
        if self.is_enabled:
            if self.pos is not None:
                painter.setRenderHint(QPainter.Antialiasing)

                painter.setPen(self.properties.get_pen())
                painter.drawLine(self.pos.x(), 0, self.pos.x(), drawRect.height())

                self.draw_pointer(painter, drawRect, scale)

    def getScale(self):
        return self.scale

    def get_pointerTimePos(self):
        return (self.pointerPos * self.getScale())

    def updateScale(self, newScale):
        if (self.scale != newScale):
            self.scale = newScale

    # Updates the position and scale of the reference marker
    def update_position(self, pos, scale):
        self.pos = pos
        x = self.pos.x()
        self.pointerPos = x
        self.updateScale(scale)



class ReferenceMarkerManager(QObject):

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.markers = dict()

    def get_scale(self):
        return self.parent().getScale()

    def add_reference_marker(self, with_identifier, properties=TickProperties(QColor(250, 187, 187), 0.9, Qt.SolidLine), position=QPoint(0.0, 0.0)):
        new_obj = ReferenceMarker(with_identifier, True, properties=properties, parent=self)
        new_obj.update_position(position, self.get_scale())

        self.markers[with_identifier] = new_obj

    def get_markers(self):
        return self.markers

    def draw(self, painter, event, scale):
        for (id_key, value) in self.markers.items():
            value.draw(painter, event, scale)





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

        # Reference Manager:
        self.referenceManager = ReferenceMarkerManager(parent=self)
        self.referenceManager.add_reference_marker("0", properties=TickProperties(QColor(250, 187, 187), 0.9, Qt.SolidLine), position=QPoint(100.0, 0.0))
        self.referenceManager.add_reference_marker("1", properties=TickProperties(QColor(187, 250, 187), 0.9, Qt.SolidLine), position=QPoint(200.0, 0.0))
        self.referenceManager.add_reference_marker("2", properties=TickProperties(QColor(187, 187, 250), 0.9, Qt.SolidLine), position=QPoint(300.0, 0.0))

        # Set variables
        self.backgroundColor = __backgroudColor__
        self.pos = None
        self.video_pos = None
        self.pointerPos = None
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

    def paintRect(self, event):
        qp = QPainter()
        qp.begin(self)
        qp.setRenderHint(QPainter.Antialiasing)

        self.draw_tick_lines(qp)
        self.draw_indicator_lines(qp)

        print("paintRect({0})".format(str(event)))
        curr_pos = QPoint((float(self.width()) * 0.10), 0.0)
        self.referenceManager.get_markers()["0"].update_position(curr_pos, self.getScale())

        curr_pos = QPoint((float(self.width()) * 0.20), 0.0)
        self.referenceManager.get_markers()["1"].update_position(curr_pos, self.getScale())

        curr_pos = QPoint((float(self.width()) * 0.30), 0.0)
        self.referenceManager.get_markers()["2"].update_position(curr_pos, self.getScale())

        self.referenceManager.draw(qp, event.rect(), self.getScale())

        # # Clear clip path
        # path = QPainterPath()
        # path.addRect(self.rect().x(), self.rect().y(), self.rect().width(), self.rect().height())
        # qp.setClipPath(path)

        qp.end()

    # Mouse movement
    def mouseMoveRect(self, e):
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
    def mousePressRect(self, e):
        if e.button() == Qt.LeftButton:
            x = e.pos().x()
            self.pointerPos = x
            self.positionChanged.emit(x)
            self.pointerTimePos = self.pointerPos * self.getScale()

            self.update()
            self.clicking = True  # Set clicking check to true

    # Mouse release
    def mouseReleaseRect(self, e):
        if e.button() == Qt.LeftButton:
            self.clicking = False  # Set clicking check to false

    # Enter
    def enterRect(self, e):
        self.is_in = True
        self.is_driven_externally = False

    # Leave
    def leaveRect(self, e):
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

    @pyqtSlot(float)
    def on_update_selected_position(self, pointer_desired_x):
        self.pointerPos = pointer_desired_x
        self.positionChanged.emit(pointer_desired_x)
        self.pointerTimePos = self.pointerPos * self.getScale()
        self.update()


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