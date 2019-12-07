import sys
from datetime import datetime, timezone, timedelta
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import Qt, QPoint, QLine, QRect, QRectF, pyqtSignal, pyqtSlot, QObject, QMargins
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush, QPalette, QPen, QPolygon, QPainterPath, QPixmap
from PyQt5.QtWidgets import QWidget, QFrame, QScrollArea, QVBoxLayout, QGridLayout, QListWidget
import os

# ReferenceMarker.py
from GUI.Model.ModelViewContainer import ModelViewContainer
from GUI.Model.TrackConfigs.AbstractTrackConfigs import TrackCache



# from GUI.Model.ReferenceLines.ReferenceMarker import RepresentedTimeRange
"""
RepresentedMarkerTime: a simple model object that wraps a datetime. To be used by ReferenceMarkerManager
"""
class RepresentedMarkerTime(QObject):
    def __init__(self, markerDatetime, parent=None):
        super(RepresentedMarkerTime, self).__init__(parent=parent)
        self._representedDatetime = markerDatetime

    @property
    def time(self):
        return self._representedDatetime

    @property
    def time_string(self):
        return self.time.strftime("%Y-%m-%d")

    # Setters:
    @time.setter
    def time(self, new_value):
        if self._representedDatetime != new_value:
            self._representedDatetime = new_value
        else:
            # Otherwise nothing has changed
            pass



class RepresentedMarkerRecord(RepresentedMarkerTime):
    def __init__(self, markerDatetime, parent=None):
        super(RepresentedMarkerRecord, self).__init__(markerDatetime, parent=parent)
        

# ReferenceMarkerManagerConfiguration: a class that holds the settings for a timeline track
class ReferenceMarkerManagerConfiguration(QObject):

    cacheUpdated = pyqtSignal()

    def __init__(self, parent=None):
        super(ReferenceMarkerManagerConfiguration, self).__init__(parent=parent)
        self.cache = TrackCache([], parent=parent)

    def filter_records(self, session):
        return self.get_filter().build_filter(session)

    # reload(...): called when the filter is changed to update the cache (reloading the records from the database) as needed
    def reload(self, session, owning_parent_track):
        found_records = self.filter_records(session)
        print("track[{0}]: {1} records found".format(self.get_track_id(), len(found_records)))

        # Build the corresponding GUI objects
        built_model_view_container_array = []
        for (index, aRecord) in enumerate(found_records):
            aGuiView = self.get_filter().trackRecordClass.get_gui_view(aRecord, parent=owning_parent_track)
            aModelViewContainer = ModelViewContainer(aRecord, aGuiView)
            built_model_view_container_array.append(aModelViewContainer)

        self.update_cache(built_model_view_container_array)

    # called to update the cache from an external source. Also called internally in self.reload(...)
    def update_cache(self, newCachedModelViewArray):
        self.cache.set_model_view_array(newCachedModelViewArray)
        self.cacheUpdated.emit()

    def get_cache(self):
        return self.cache


"""
RepresentedTimeRange: on object that holds a reference to the current global start and end times
"""
class RepresentedTimeRange(QObject):

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


