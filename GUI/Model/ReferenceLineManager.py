#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ReferenceLineManager.py
import queue
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QPoint, QLine, QRect, QRectF, pyqtSignal, pyqtSlot, QObject, QMargins
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPalette, QPen, QPolygon, QPainterPath, QPixmap
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea, QVBoxLayout
import sys
import os


## IMPORTS:
# from GUI.Model.ReferenceLineManager import TickProperties, ReferenceMarker, ReferenceMarkerManager

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

    # L = queue.Queue(maxsize=20)

    def __init__(self, num_markers, parent=None):
        super().__init__(parent=parent)
        self.used_mark_stack = []
        self.markers = dict()
        self.bulk_add_reference_makers(num_markers)

    def get_scale(self):
        return self.parent().getScale()

    def bulk_add_reference_makers(self, num_markers):
        self.used_mark_stack = []
        self.markers = dict()
        for a_marker_index in range(num_markers):
            curr_color = QColor.fromHslF((float(a_marker_index)/float(num_markers)), 0.9, 0.9, 1.0)
            curr_properties = TickProperties(curr_color, 0.9, Qt.SolidLine)
            new_obj = ReferenceMarker(str(a_marker_index), False, properties=curr_properties, parent=self)
            curr_pos = QPoint(0.0, 0.0)
            new_obj.update_position(curr_pos, self.get_scale())
            self.markers[str(a_marker_index)] = new_obj

    # def add_reference_marker(self, with_identifier, properties=TickProperties(QColor(250, 187, 187), 0.9, Qt.SolidLine), position=QPoint(0.0, 0.0)):
    #     new_obj = ReferenceMarker(with_identifier, True, properties=properties, parent=self)
    #     new_obj.update_position(position, self.get_scale())
    #     self.markers[with_identifier] = new_obj

    # Returns the next unused marker so it can be used
    def get_next_unused_marker(self):
        for (aKey, aValue) in self.get_markers().items():
            if (not aValue.is_enabled):
                return aKey
            else:
                continue
        return None

    # Called to update the position of the next unused marker (making it used)
    def update_next_unused_marker(self, new_position):
        potential_unused_marker_key = self.get_next_unused_marker()
        if (potential_unused_marker_key is None):
            print("ERROR: no unused markers available. Need to implement reuse")
            return
        else:
            self.get_markers()[potential_unused_marker_key].update_position(new_position, self.get_scale())
            self.get_markers()[potential_unused_marker_key].is_enabled = True
            # Add the key of the now used item to the used_stack
            self.used_mark_stack.append(potential_unused_marker_key)


    def get_last_used_markers(self, max_num):
        actual_max_num = min(max_num, len(self.used_mark_stack))
        out_objs = []
        curr_pop_count = 0
        while curr_pop_count < actual_max_num:
            out_objs.append(self.used_mark_stack.pop())
            curr_pop_count = curr_pop_count + 1
        else:
            print("popped {0} objects".format(str(len(out_objs))))
        return out_objs



    def get_markers(self):
        return self.markers

    def draw(self, painter, event, scale):
        for (id_key, value) in self.markers.items():
            value.draw(painter, event, scale)

