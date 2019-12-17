import sys
from enum import Enum
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget,QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize, pyqtSlot

## IMPORT:
# from GUI.Model.TrackType import TrackType, TrackStorageArray

class TrackStorageArray(Enum):
    Unknown = 1
    Video = 2
    Event = 3


class TrackType(Enum):
    Unknown = 1
    Video = 2
    Annotation = 3
    Partition = 4
    DataFile = 5

    def get_short_str(self):
        if self == TrackType.Unknown:
            return '?'
        elif self == TrackType.Video:
            return 'V'
        elif self == TrackType.Annotation:
            return 'A'
        elif self == TrackType.Partition:
            return 'P'
        elif self == TrackType.DataFile:
            return 'D'
        else:
            return '!'

    def get_medium_str(self):
        if self == TrackType.Unknown:
            return '???'
        elif self == TrackType.Video:
            return 'Vid'
        elif self == TrackType.Annotation:
            return 'Note'
        elif self == TrackType.Partition:
            return 'Part'
        elif self == TrackType.DataFile:
            return 'Data'
        else:
            return 'ERR'

    def get_long_str(self):
        if self == TrackType.Unknown:
            return 'Unknown'
        elif self == TrackType.Video:
            return 'Video'
        elif self == TrackType.Annotation:
            return 'Annotation'
        elif self == TrackType.Partition:
            return 'Partition'
        elif self == TrackType.DataFile:
            return 'DataFile'
        else:
            return 'ERROR'


    def get_storage_array_type(self):
        if self == TrackType.Unknown:
            return TrackStorageArray.Unknown
        elif self == TrackType.Video:
            return TrackStorageArray.Video
        elif self == TrackType.Annotation:
            return TrackStorageArray.Event
        elif self == TrackType.Partition:
            return TrackStorageArray.Event
        elif self == TrackType.DataFile:
            return TrackStorageArray.Event
        else:
            return TrackStorageArray.Unknown



    def get_default_track_height(self):
        defaultMinimumVideoTrackHeight = 50
        defaultMinimumEventTrackHeight = 50

        if self == TrackType.Unknown:
            return defaultMinimumEventTrackHeight
        elif self == TrackType.Video:
            return defaultMinimumVideoTrackHeight
        elif self == TrackType.Annotation:
            return defaultMinimumEventTrackHeight
        elif self == TrackType.Partition:
            return defaultMinimumEventTrackHeight
        elif self == TrackType.DataFile:
            return 25 # Data tracks are smaller
        else:
            return defaultMinimumEventTrackHeight



    def __str__(self):
        return self.get_long_str()



# TrackConfigMixin: Used to get the config 
class TrackConfigMixin(object):
    # Track config functions
    def get_track_config(self):
        return self.trackConfig

    def get_track_filter(self):
        return self.get_track_config().get_filter()

    def get_track_type(self):
        return self.get_track_filter().get_track_type()

""" TrackConfigDataCacheMixin:
This object has a config with a cache that caches both its active record and view objects. 
"""
class TrackConfigDataCacheMixin(object):

    # Gets the container array from the cache
    @pyqtSlot()
    def get_cached_container_array(self):
        active_cache = self.trackConfig.get_cache()
        active_model_view_array = active_cache.get_model_view_array()
        return active_model_view_array

    @pyqtSlot()
    def get_cached_duration_records(self):
        return self.durationRecords

    # TODO: durationObjects aren't populated correctly for partition tracks because they're stored in the partition manager
    @pyqtSlot()
    def get_cached_duration_views(self):
        return self.durationObjects

    # performReloadConfigCache(...): actually tells the config cache to update
    @pyqtSlot()
    def performReloadConfigCache(self):
        self.get_track_config().reload(self.database_connection.get_session(), self)
