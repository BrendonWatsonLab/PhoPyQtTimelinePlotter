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
# from GUI.Model.ReferenceLines.ReferenceLineManager import ReferenceMarkerManager

from GUI.Model.ReferenceLines.ReferenceMarkerVisualHelpers import TickProperties, ReferenceMarker
from GUI.Model.ReferenceLines.ReferenceMarker import RepresentedTimeRange, RepresentedMarkerTime

__textColor__ = QColor(20, 20, 20)
__font__ = QFont('Decorative', 12)




"""
ReferenceMarkerManager is a shared singleton that defines the positions of "reference lines" that are drawn throughout the main timeline.
"""
"""
Want to have an array of datetimes at which to plot tick lines.
The widget's current size is used, along with the totalStartTime and totalEndTime, to compute the positions at which to draw the tick lines and labels.
"""
class ReferenceMarkerManager(QObject):

    used_markers_updated = pyqtSignal(list)
    
    wants_extended_data = pyqtSignal(list)
    used_markers_extended_data_updated = pyqtSignal(list)

    selection_changed = pyqtSignal(list, list)

    # L = queue.Queue(maxsize=20)

    def __init__(self, num_markers, parent=None):
        super().__init__(parent=parent)
        self.staticMarkerData = []
        # RepresentedMarkerTime
        self.activeMarkersWindow = None
        self.used_mark_stack = []
        self.used_mark_extended_metadata_stack = []
        self.markers = dict()
        self.bulk_add_reference_makers(num_markers)

    def get_scale(self):
        return self.parent().getScale()

    def get_used_markers(self):
        return [self.get_markers()[aKey] for aKey in self.used_mark_stack]

    @staticmethod
    def daterange(start_date, end_date):
        for n in range(int ((end_date - start_date).days)):
            yield start_date + timedelta(n)
            

    def bulk_add_static_marker_data(self):
        self.staticMarkerData = []
        start_date = self.totalStartTime
        end_date = self.totalEndTime
        for single_date in ReferenceMarkerManager.daterange(start_date, end_date):
            # print(single_date.strftime("%Y-%m-%d"))
            newObj = RepresentedMarkerTime(single_date, self)
            print(newObj.time_string)
            self.staticMarkerData.append(newObj)


    def get_static_marker_data(self):
        return self.staticMarkerData

        # for single_date in (start_date_day + timedelta(n) for n in range(day_count)):
        #     print(single_date.strftime("%Y-%m-%d"))
        

    def bulk_add_reference_makers(self, num_markers):
        self.used_mark_stack = []
        self.used_mark_extended_metadata_stack = []
        self.markers = dict()
        for a_marker_index in range(num_markers):
            curr_color = QColor.fromHslF((float(a_marker_index)/float(num_markers)), 0.9, 0.9, 1.0)
            curr_properties = TickProperties(curr_color, 0.9, Qt.SolidLine)
            new_obj = ReferenceMarker(str(a_marker_index), False, properties=curr_properties, parent=self)
            new_obj.update_position(0.0, self.get_scale())
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


    # Called when the timeline changes its global represented start and end times. This will change how the reference marker data objects are mapped to positions.
    @pyqtSlot(datetime, datetime, timedelta)
    def on_global_timeline_timespan_changed(self, totalStartTime, totalEndTime, totalDuration):
        print("Reference manager: on_global_timeline_timespan_changed({0}, {1}, {2})".format(str(totalStartTime), str(totalEndTime), str(totalDuration)))


    # show_active_markers_list(): creates a list window that displays the current markers
    def show_active_markers_list(self):
        if self.activeMarkersWindow is not None:
            print("Already have a list window!")
            return

        # all_markers = self.get_last_used_markers(len(self.used_mark_stack))
        all_markers = self.get_used_markers()
        self.wants_extended_data.emit(all_markers)

        self.activeMarkersWindow = ReferenceMarkViewer(all_markers)
        self.used_markers_updated.connect(self.activeMarkersWindow.on_active_markers_list_updated)
        self.used_markers_extended_data_updated.connect(self.activeMarkersWindow.on_active_markers_metadata_updated)
        self.selection_changed.connect(self.activeMarkersWindow.selection_changed)
        self.activeMarkersWindow.show()


    # Main Window Slots:
    @pyqtSlot()
    def on_active_zoom_changed(self):
        print("ReferenceMarkerManager.on_active_zoom_changed(...)")
        # self.update()

    @pyqtSlot()
    def on_active_viewport_changed(self):
        print("ReferenceMarkerManager.on_active_viewport_changed(...)")
        # self.update()

    @pyqtSlot(datetime, datetime, timedelta)
    def on_active_global_timeline_times_changed(self, totalStartTime, totalEndTime, totalDuration):
        print("ReferenceMarkerManager.on_active_global_timeline_times_changed({0}, {1}, {2})".format(str(totalStartTime), str(totalEndTime), str(totalDuration)))
        self.totalStartTime = totalStartTime
        self.totalEndTime = totalEndTime
        self.totalDuration = totalDuration
        self.bulk_add_static_marker_data()
        # self.update()
        return