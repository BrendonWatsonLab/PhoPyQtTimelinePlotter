#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ReferenceLineManager.py
import queue
import numpy as np

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QPoint, QLine, QRect, QRectF, pyqtSignal, pyqtSlot, QObject, QMargins
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPalette, QPen, QPolygon, QPainterPath, QPixmap
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea, QVBoxLayout, QGridLayout, QListWidget
import sys
import os

from GUI.UI.ReferenceMarkViewer.ReferenceMarkViewer import ReferenceMarkViewer, ActiveReferenceMarkersMixin

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

    def get_position_tuple_string(self):
        return '(pos: {0}, pointerPos: {1}, get_pointerTimePos: {2})'.format(self.pos, self.pointerPos, self.get_pointerTimePos())

    def __str__(self):
        return 'RefMark[identifier: {0}]: {1}'.format(self.identifier, self.get_position_tuple_string())


class ReferenceMarkerManager(QObject):

    used_markers_updated = pyqtSignal(list)
    
    wants_extended_data = pyqtSignal(list)
    used_markers_extended_data_updated = pyqtSignal(list)

    selection_changed = pyqtSignal(list, list)

    

    # L = queue.Queue(maxsize=20)

    def __init__(self, num_markers, parent=None):
        super().__init__(parent=parent)
        self.activeMarkersWindow = None
        self.used_mark_stack = []
        self.used_mark_extended_metadata_stack = []
        self.markers = dict()
        self.bulk_add_reference_makers(num_markers)

    def get_scale(self):
        return self.parent().getScale()

    def get_used_markers(self):
        return [self.get_markers()[aKey] for aKey in self.used_mark_stack]
        

    def bulk_add_reference_makers(self, num_markers):
        self.used_mark_stack = []
        self.used_mark_extended_metadata_stack = []
        self.markers = dict()
        for a_marker_index in range(num_markers):
            curr_color = QColor.fromHslF((float(a_marker_index)/float(num_markers)), 0.9, 0.9, 1.0)
            curr_properties = TickProperties(curr_color, 0.9, Qt.SolidLine)
            new_obj = ReferenceMarker(str(a_marker_index), False, properties=curr_properties, parent=self)
            curr_pos = QPoint(0.0, 0.0)
            new_obj.update_position(curr_pos, self.get_scale())
            self.markers[str(a_marker_index)] = new_obj

        self.used_markers_updated.emit(self.get_used_markers())

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

            self.show_active_markers_list()
            self.used_markers_updated.emit(self.get_used_markers())
            self.wants_extended_data.emit(self.get_used_markers())


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

    @pyqtSlot(list)
    def update_marker_metadata(self, marker_metadata_list):
        self.used_mark_extended_metadata_stack = marker_metadata_list
        self.used_markers_extended_data_updated.emit(self.used_mark_extended_metadata_stack)

    # show_active_markers_list(): creates a list window that displays the current markers
    def show_active_markers_list(self):
        if self.activeMarkersWindow is not None:
            print("Already have a list window!")
            return

        # all_markers = self.get_last_used_markers(len(self.used_mark_stack))
        all_markers = self.get_used_markers()
        self.wants_extended_data.emit(all_markers)

        # self.activeMarkersWindow = ActiveReferenceMarkersWindow(all_markers)
        # self.used_markers_updated.connect(self.activeMarkersWindow.on_active_markers_list_updated)
        # self.used_markers_extended_data_updated.connect(self.activeMarkersWindow.on_active_markers_metadata_updated)
        # self.selection_changed.connect(self.activeMarkersWindow.selection_changed)
        # self.activeMarkersWindow.show()

        self.activeMarkersWindow = ReferenceMarkViewer(all_markers)
        self.used_markers_updated.connect(self.activeMarkersWindow.on_active_markers_list_updated)
        self.used_markers_extended_data_updated.connect(self.activeMarkersWindow.on_active_markers_metadata_updated)
        self.selection_changed.connect(self.activeMarkersWindow.selection_changed)
        self.activeMarkersWindow.show()



class ActiveReferenceMarkersWindow(ActiveReferenceMarkersMixin, QWidget):


    def __init__(self, activeMarkersList):
        QWidget.__init__(self)
        self.activeMarkersList = activeMarkersList
        self.activeMetadataList = np.repeat(None, len(activeMarkersList))
        self.setWindowTitle("Active Reference Marks")

        layout = QGridLayout()
        self.setLayout(layout)
        self.listwidget = QListWidget()
        self.listwidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.listwidget.itemClicked.connect(self.on_item_clicked)
        # self.listwidget.clicked.connect(self.clicked)
        layout.addWidget(self.listwidget)

        self.reload_list()

    def reload_list(self):
        self.listwidget.clear()
        for (anIndex, anItem) in enumerate(self.activeMarkersList):
            curr_string = ""
            if self.activeMetadataList[anIndex] is None:
                curr_string = str(anItem)
            else:
                curr_metadata_item = self.activeMetadataList[anIndex]
                curr_string = ('RefMark[identifier: {0}]: (datetime: {1})'.format(anItem.identifier, str(curr_metadata_item)))
                # curr_string = str(anItem) + str(self.activeMetadataList[anIndex])

            # Create the new table item            
            curr_item = QtWidgets.QListWidgetItem(curr_string)

            # Add it to the table
            self.listwidget.insertItem(anIndex, curr_item)


    def on_item_clicked(self):
        selected_items = self.listwidget.selectedItems()
        selected_indicies = []
        for index in range(len(selected_items)):
            aSelectedItem = selected_items[index]
            currRow = self.listwidget.row(aSelectedItem)
            selected_indicies.append(currRow)

        print("Selected indicies: {0}".format(str(selected_indicies)))
        self.selection_changed.emit(self.activeMarkersList, selected_indicies)
        return

    def get_selected_items(self):
        return self.listwidget.selectedItems()
        

    def get_selected_item_indicies(self):
        selected_items = self.get_selected_items()
        selected_indicies = []
        for index in range(len(selected_items)):
            aSelectedItem = selected_items[index]
            currRow = self.listwidget.row(aSelectedItem)
            selected_indicies.append(currRow)

        return selected_indicies


    # def clicked(self, qmodelindex):
    #     itemIndex = self.listwidget.currentRow()
    #     item = self.listwidget.currentItem()
    #     print(item.text())
    #     self.selection_changed.emit(self.activeMarkersList, itemIndex)

    # @pyqtSlot(list)
    # def on_active_markers_list_updated(self, newList):
    #     self.activeMarkersList = newList
    #     self.activeMetadataList = np.repeat(None, len(self.activeMarkersList)) # Clear the metadata
    #     self.reload_list()

    # @pyqtSlot(list)
    # def on_active_markers_metadata_updated(self, newMetadata):
    #     self.activeMetadataList = newMetadata
    #     self.reload_list()
