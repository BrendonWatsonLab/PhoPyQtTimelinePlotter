#!/usr/bin/python3
# -*- coding: utf-8 -*-
# ReferenceLineManager.py
import sys
from datetime import datetime, timezone, timedelta, time
import time as timen
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

from GUI.Model.ModelViewContainer import ModelViewContainer
from GUI.Model.ReferenceLines.ReferenceMarkerVisualHelpers import TickProperties, ReferenceMarker
from GUI.Model.ReferenceLines.ReferenceMarker import RepresentedTimeRange, RepresentedMarkerTime, RepresentedMarkerRecord, ReferenceMarkerManagerConfiguration
from GUI.Helpers.DurationRepresentationHelpers import DurationRepresentationMixin


__textColor__ = QColor(20, 20, 20)
__font__ = QFont('Decorative', 12)


"""
ReferenceMarkerManager is a shared singleton that defines the positions of "reference lines" that are drawn throughout the main timeline.
"""
"""
Want to have an array of datetimes at which to plot tick lines.
The widget's current size is used, along with the totalStartTime and totalEndTime, to compute the positions at which to draw the tick lines and labels.
"""
class ReferenceMarkerManager(DurationRepresentationMixin, QObject):

    used_markers_updated = pyqtSignal(list)
    
    wants_extended_data = pyqtSignal(list)
    used_markers_extended_data_updated = pyqtSignal(list)

    selection_changed = pyqtSignal(list, list)

    # L = queue.Queue(maxsize=20)

    def __init__(self, totalStartTime, totalEndTime, drawWidth, num_markers, parent=None):
        super().__init__(parent=parent)
        self.totalStartTime = totalStartTime
        self.totalEndTime = totalEndTime
        self.totalDuration = self.get_total_duration()
        self.drawWidth = drawWidth


        self.minorMarkersHoursSpacing = 4

        # self.config = ReferenceMarkerManagerConfiguration(parent=self)
        # self.trackConfig.cacheUpdated.connect(self.on_reloadModelFromConfigCache)
        # self.markerRecordsDict = dict()
        # self.markerViewsDict = dict()
        self.markersDict = dict()
        self.needs_positions_update = True

        self.staticDaysMarkerData = []
        self.staticMinorMarkerData = []

        # RepresentedMarkerTime
        self.activeMarkersWindow = None
        self.used_mark_stack = []
        self.used_mark_extended_metadata_stack = []

        self.bulk_add_reference_makers(num_markers)
        self.bulk_add_static_marker_data()

        
    def get_scale(self):
        return self.parent().getScale()

    def get_used_markers(self):
        return [self.get_markers()[aKey] for aKey in self.used_mark_stack]



    # Returns the start of the day
    @staticmethod
    def start_of_day(aDate):
        return datetime.combine(aDate, time())

    # Returns 1 microsecond before the end of the day
    @staticmethod
    def end_of_day(aDate):
        tomorrow = aDate + timedelta(days=1)
        start_of_tomorrow = ReferenceMarkerManager.start_of_day(tomorrow)
        return (start_of_tomorrow - timedelta(microseconds=1))


    # Returns true if the date is the start of the day
    @staticmethod
    def is_start_of_day(aDate):
        start_of_day = ReferenceMarkerManager.start_of_day(aDate)
        return (aDate == start_of_day)

    # Returns true if the date is 1 microsecond before the end of the day
    @staticmethod
    def is_end_of_day(aDate):
        end_of_day = ReferenceMarkerManager.end_of_day(aDate)
        return (aDate == end_of_day)

    @staticmethod
    def daterange(start_date, end_date):
        for n in range(int ((end_date - start_date).days)):
            yield ReferenceMarkerManager.start_of_day(start_date + timedelta(n))

    # secondsBetween(start_date, end_date): returns the total number of seconds between two datetimes
    @staticmethod
    def secondsBetween(start_date, end_date):
        return timen.mktime(end_date.timetuple()) - timen.mktime(start_date.timetuple()) 

    @staticmethod
    def minor_markers_daterange(start_date, end_date, hoursBetween):
        # TODO: Zero seconds
        hours_only_start_date = datetime(year=start_date.year, month=start_date.month, day=start_date.day, hour=start_date.hour, minute=0, second=0, tzinfo=start_date.tzinfo)
        hoursDelta = timedelta(hours=hoursBetween)


        numSecondsBetween = int(ReferenceMarkerManager.secondsBetween(start_date, end_date))
        numHoursBetween = int(float(numSecondsBetween)/3600.0)


        for n in range(numHoursBetween):
            potential_marker = hours_only_start_date + timedelta(hours=n)
            # make sure the potential marker is between the two dates.
            if (start_date <= potential_marker <= end_date):
                # If it's not the start of the day, return it
                if (not ReferenceMarkerManager.is_start_of_day(potential_marker)):
                    yield potential_marker



        # Need to do proper date math to get hours since .hours doesn't work.
        # for n in range(int (((end_date - hours_only_start_date).days*24))):
        #     potential_marker = start_date + (n* hoursDelta)
        #     # If it's not the start of the day, return it
        #     if (not ReferenceMarkerManager.is_start_of_day(potential_marker)):
        #         yield potential_marker  


    def bulk_add_static_marker_data(self):
        self.staticDaysMarkerData = []
        self.staticMinorMarkerData = []
        start_date = self.totalStartTime
        end_date = self.totalEndTime
        # builds major (day) markers
        for single_date in ReferenceMarkerManager.daterange(start_date, end_date):
            newObj = RepresentedMarkerTime(single_date, self)
            print(newObj.time_string)
            self.staticDaysMarkerData.append(newObj)

        # builds minor markers separated by self.minorMarkersHoursSpacing hours
        for single_date in ReferenceMarkerManager.minor_markers_daterange(start_date, end_date, self.minorMarkersHoursSpacing):
            newObj = RepresentedMarkerTime(single_date, self)
            print(newObj.time_string)
            self.staticMinorMarkerData.append(newObj)


        


    def get_static_major_marker_data(self):
        return self.staticDaysMarkerData
        
    def get_static_minor_marker_data(self):
        return self.staticMinorMarkerData

    def bulk_add_reference_makers(self, num_markers):
        self.used_mark_stack = []
        self.used_mark_extended_metadata_stack = []
        self.needs_positions_update = True
        # self.markerRecordsDict = dict()
        # self.markerViewsDict = dict()
        self.markersDict = dict()

        for a_marker_index in range(num_markers):
            curr_color = QColor.fromHslF((float(a_marker_index)/float(num_markers)), 0.9, 0.9, 1.0)
            curr_properties = TickProperties(curr_color, 0.9, Qt.SolidLine)
            new_view_obj = ReferenceMarker(str(a_marker_index), False, properties=curr_properties, parent=self)
            new_view_obj.update_position(0.0, self.get_scale())

            new_record_obj = RepresentedMarkerRecord(datetime.now(), parent=self)
            aModelViewContainer = ModelViewContainer(new_record_obj, new_view_obj)

            self.markersDict[str(a_marker_index)] = aModelViewContainer

        self.used_markers_updated.emit(self.get_used_markers())

    # def add_reference_marker(self, with_identifier, properties=TickProperties(QColor(250, 187, 187), 0.9, Qt.SolidLine), position=QPoint(0.0, 0.0)):
    #     new_obj = ReferenceMarker(with_identifier, True, properties=properties, parent=self)
    #     new_obj.update_position(position, self.get_scale())
    #     self.markers[with_identifier] = new_obj

    # Returns the next unused marker so it can be used
    def get_next_unused_marker_key(self):
        for (aKey, aValue) in self.get_markers().items():
            if (not aValue.get_view().is_enabled):
                return aKey
            else:
                continue
        return None

    # Called to update the position of the next unused marker (making it used)
    # def update_next_unused_marker(self, new_position):
    #     potential_unused_marker_key = self.get_next_unused_marker()
    #     if (potential_unused_marker_key is None):
    #         print("ERROR: no unused markers available. Need to implement reuse")
    #         return
    #     else:
    #         self.get_markers()[potential_unused_marker_key].update_position(new_position, self.get_scale())
    #         self.get_markers()[potential_unused_marker_key].is_enabled = True
    #         # Add the key of the now used item to the used_stack
    #         self.used_mark_stack.append(potential_unused_marker_key)

    #         self.show_active_markers_list()
    #         self.used_markers_updated.emit(self.get_used_markers())
    #         self.wants_extended_data.emit(self.get_used_markers())

    def update_next_unused_marker(self, new_datetime, currDrawWidth):
        self.drawWidth = currDrawWidth
        potential_unused_marker_key = self.get_next_unused_marker_key()
        if (potential_unused_marker_key is None):
            print("ERROR: no unused markers available. Need to implement reuse")
            return
        else:
            # Create a new record objecct
            self.get_markers()[potential_unused_marker_key].get_record().time = new_datetime

            # Get the x_offset position from the datetime provided
            # item_x_offset = self.compute_x_offset_from_datetime(new_datetime)

            self.get_markers()[potential_unused_marker_key].get_view().update_position(0.0, self.get_scale())
            self.get_markers()[potential_unused_marker_key].get_view().is_enabled = True
            
            self.needs_positions_update = True

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
        return self.markersDict

    # def get_marker_views(self):
    #     return self.markerViewsDict

    # def get_marker_records(self):
    #     return self.markerRecordsDict

    # Given the percent offset of the total duration, gets the x-offset for the timeline tracks (not the viewport, its contents)
    @staticmethod
    def percent_offset_to_track_offset(drawWidth, track_percent):
        return float(drawWidth) * float(track_percent)


    # def percent_offset_to_track_offset(self, track_percent):
    #     return float(self.drawWidth) * float(track_percent)

    # compute_x_offset_from_datetime(aDatetime): depends on current duration and width
    def compute_x_offset_from_datetime(self, drawWidth, aDatetime):
        item_percent_offset = self.datetime_to_percent(aDatetime)
        item_x_offset = ReferenceMarkerManager.percent_offset_to_track_offset(drawWidth, item_percent_offset)
        return item_x_offset



    def draw(self, painter, event, scale):
        # drawWidth = event.width()
        drawWidth = self.drawWidth
        # self.drawWidth = event.width()
        for (id_key, value) in self.markersDict.items():
            # Get the datetime from the record:
            if self.needs_positions_update:
                currRecord = value.get_record()
                itemDatetime = currRecord.time
                item_x_offset = self.compute_x_offset_from_datetime(drawWidth, itemDatetime)
                value.get_view().update_position(item_x_offset, self.get_scale())
            # Draw the correctly updated record
            value.get_view().draw(painter, event, scale)

        if self.needs_positions_update:
            # we've done the positions update at this point, so turn off the flag
            self.needs_positions_update = False

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
        self.needs_positions_update = True

    @pyqtSlot()
    def on_active_viewport_changed(self):
        print("ReferenceMarkerManager.on_active_viewport_changed(...)")
        self.needs_positions_update = True
        # self.update()

    @pyqtSlot(datetime, datetime, timedelta)
    def on_active_global_timeline_times_changed(self, totalStartTime, totalEndTime, totalDuration):
        print("ReferenceMarkerManager.on_active_global_timeline_times_changed({0}, {1}, {2})".format(str(totalStartTime), str(totalEndTime), str(totalDuration)))
        self.totalStartTime = totalStartTime
        self.totalEndTime = totalEndTime
        self.totalDuration = totalDuration
        self.bulk_add_static_marker_data()
        self.needs_positions_update = True
        # self.update()
        return


    # Called on the width changing
    @pyqtSlot(float) 
    def set_fixed_width(self, newWidth):
        self.drawWidth = newWidth
        # todo: rebuild the item?
        self.needs_positions_update = True