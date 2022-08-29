# -*- coding: utf-8 -*-
# DurationRepresentationHelpers.py
import sys
from enum import Enum
from datetime import datetime, timezone, timedelta
from PyQt5.QtWidgets import QFrame
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize



class RepresentedTimeRange(QObject):
    """ RepresentedTimeRange: on object that holds a reference to the current global start and end times
    """
    timesChanged = pyqtSignal(datetime, datetime, timedelta) # Called when the timeline's global displayed start/end times are updated
    
    def __init__(self, totalStartTime, totalEndTime, parent=None):
        super(RepresentedTimeRange, self).__init__(parent=parent)
        self._totalStartTime = totalStartTime
        self._totalEndTime = totalEndTime
        self._totalDuration = (totalEndTime - totalStartTime)

    # Getters:
    @property
    def totalStartTime(self):
        return self._totalStartTime

    @property
    def totalEndTime(self):
        return self._totalEndTime

    @property
    def totalDuration(self):
        return (self.totalEndTime - self.totalStartTime)

    # Setters:
    @totalStartTime.setter
    def totalStartTime(self, new_value):
        if self._totalStartTime != new_value:
            self._totalStartTime = new_value
            self.timesChanged.emit(self.totalStartTime, self.totalEndTime, self.totalDuration)
        else:
            # Otherwise nothing has changed
            pass

    @totalEndTime.setter
    def totalEndTime(self, new_value):
        if self._totalEndTime != new_value:
            self._totalEndTime = new_value
            self.timesChanged.emit(self.totalStartTime, self.totalEndTime, self.totalDuration)
        else:
            # Otherwise nothing has changed
            pass





## IMPORTS:
# from phopyqttimelineplotter.GUI.Helpers.DurationRepresentationHelpers import DurationRepresentationMixin

class DurationRepresentationMixin(object):

    """
        Object must have the following instance properties:
        self.width()
        self.height()

        self.totalStartTime
        self.totalEndTime
        self.activeScaleMultiplier
    """

    def get_total_start_time(self):
        return self.totalStartTime

    def get_total_end_time(self):
        return self.totalEndTime

    def get_total_duration(self):
        return (self.get_total_end_time() - self.get_total_start_time())

    # Timeline position/time converion functions:
    def datetime_to_percent(self, newDatetime):
        duration_offset = newDatetime - self.totalStartTime
        percent_x = duration_offset / self.totalDuration
        return percent_x

    ## Datetime functions copied from the versions created for the PhoDurationEvent class
    # returns true if the absolute_datetime falls within the current entire timeline. !Not the viewport!
    def contains_date(self, absolute_datetime):
        return ((self.get_total_start_time() <= absolute_datetime) and (self.get_total_end_time() >= absolute_datetime))

    # Returns the duration of the time relative to this timeline.
    def compute_relative_offset_duration(self, time):
        relative_offset_duration = time - self.get_total_start_time()
        return relative_offset_duration

    # Returns the absolute (wall/world) time for a relative_duration into the timeline
    def compute_absolute_time(self, relative_duration):
        return (self.get_total_start_time() + relative_duration)




## Unused:
class OffsetRepresentationMixin(object):

    """
        Object must have the following instance properties:
        self.width()
        self.height()

        self.totalStartTime
        self.totalEndTime
        self.activeScaleMultiplier
    """

    def get_total_start_time(self):
        return self.totalStartTime

    def get_total_end_time(self):
        return self.totalEndTime

    def get_total_duration(self):
        return (self.get_total_end_time() - self.get_total_start_time())

    def get_active_scale_multiplier(self):
        return self.activeScaleMultiplier

    # Get scale from length
    def getScale(self):
        return float(self.get_total_duration())/float(self.width())


    # Timeline position/time converion functions:
    def offset_to_percent(self, event_x, event_y):
        percent_x = event_x / (self.width() * self.get_active_scale_multiplier())
        percent_y = event_y / self.height()
        return (percent_x, percent_y)

    def offset_to_duration(self, event_x):
        (percent_x, percent_y) = self.offset_to_percent(event_x, 0.0)
        return (self.get_total_duration() * percent_x)

    def offset_to_datetime(self, event_x):
        duration_offset = self.offset_to_duration(event_x)
        return (self.get_total_start_time() + duration_offset)

    def percent_to_offset(self, percent_offset):
        event_x = percent_offset * (self.width() * self.get_active_scale_multiplier())
        return event_x

    def duration_to_offset(self, duration_offset):
        percent_x = duration_offset / self.get_total_duration()
        event_x = self.percent_to_offset(percent_x)
        return event_x

    def datetime_to_offset(self, newDatetime):
        duration_offset = newDatetime - self.get_total_start_time()
        event_x = self.duration_to_offset(duration_offset)
        return event_x