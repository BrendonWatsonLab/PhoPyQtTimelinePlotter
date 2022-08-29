#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
from datetime import datetime, timedelta, timezone
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import (
    QDir,
    QEvent,
    QObject,
    QPoint,
    QRect,
    QSize,
    Qt,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPen
from PyQt5.QtWidgets import (
    QAbstractScrollArea,
    QAbstractSlider,
    QAction,
    QApplication,
    QDialog,
    QFileSystemModel,
    QFormLayout,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QTreeView,
    QVBoxLayout,
    QWidget,
    qApp,
)

# TrackGroups.py

## IMPORTS:
# from phopyqttimelineplotter.GUI.Model.TrackGroups import VideoTrackGroupSettings, VideoTrackGroup, TrackReference, TrackChildReference, VideoTrackGroupOwningMixin

""" TrackChildReference: a reference to a child event on a specific track.
owningTrackReference: TrackReference
childEventObject: the actual referenced event object
"""


class TrackChildReference(QObject):
    def __init__(
        self, owningTrackReference, childEventIndex, childEventObject, parent=None
    ):
        super().__init__(parent=parent)
        self._owningTrackReference = owningTrackReference
        self._childEventIndex = childEventIndex
        self._childEventObject = childEventObject

    def get_track_id(self):
        return self._owningTrackReference.trackID

    def get_group_id(self):
        return self._owningTrackReference.groupID

    def get_childEventIndex(self):
        return self._childEventIndex

    def set_childEventIndex(self, newValue):
        self._childEventIndex = newValue

    def get_childEventObject(self):
        return self._childEventObject

    def set_childEventObject(self, newValue):
        self._childEventObject = newValue


""" TrackReference: a reference to a specific timeline track.
"""


class TrackReference(QObject):
    def __init__(self, trackID, owningTrackGroupID, parent=None):
        super().__init__(parent=parent)
        self.trackID = trackID
        self.groupID = owningTrackGroupID

    def get_track_id(self):
        return self.trackID

    def get_group_id(self):
        return self.groupID


class VideoTrackGroupOwningMixin(object):
    """
     self.trackGroups = []
    self.trackID_to_GroupIndexMap = dict() #Maps a track's trackID to the index of its group in self.trackGroups
    self.trackID_to_TrackWidgetLocatorTuple = dict() #Maps a track's trackID to the a tuple (storageArrayType: TrackStorageArray, storageArrayIndex: Int) that can be used to retreive the widget
    self.videoFileTrackWidgets = []
    self.eventTrackWidgets = []
    self.trackGroups = []
    self.trackID_to_GroupIndexMap = dict() #Maps a track's trackID to the index of its group in self.trackGroups
    self.trackID_to_TrackWidgetLocatorTuple = dict() #Maps a track's trackID to the a tuple (storageArrayType: TrackStorageArray, storageArrayIndex: Int) that can be used to retreive the widget

    self.totalTrackCount = len(self.videoFileTrackWidgets) + len(self.eventTrackWidgets)
    self.totalNumGroups = len(self.trackGroups)
    """

    def get_total_num_tracks(self):
        return len(self.videoFileTrackWidgets) + len(self.eventTrackWidgets)

    def get_total_num_groups(self):
        return len(self.trackGroups)

    # Returns the group_id from the provided track_id
    def get_group_id_from_track_id(self, trackID):
        return self.trackID_to_GroupIndexMap[trackID]


class VideoTrackGroupSettings(QObject):
    def __init__(
        self,
        wantsLabeledVideoTrack=False,
        wantsAnnotationsTrack=True,
        wantsPartitionTrack=False,
        wantedDataTracks=[],
        parent=None,
    ):
        super().__init__(parent=parent)
        self.wantsLabeledVideoTrack = wantsLabeledVideoTrack
        self.wantsAnnotationsTrack = wantsAnnotationsTrack
        self.wantsPartitionTrack = wantsPartitionTrack
        self.wantedDataTracks = wantedDataTracks

    # wantsLabeledVideoTrack, wantsAnnotationsTrack, wantsPartitionTrack, wantedDataTracks = self.get_helper_track_preferences()
    def get_helper_track_preferences(self):
        return (
            self.wantsLabeledVideoTrack,
            self.wantsAnnotationsTrack,
            self.wantsPartitionTrack,
            self.wantedDataTracks,
        )


class VideoTrackGroup(QObject):
    def __init__(
        self,
        groupID,
        videoTrackIndex=None,
        labeledVideoTrackIndex=None,
        annotationsTrackIndex=None,
        partitionsTrackIndex=None,
        dataTrackIndicies=[],
        parent=None,
    ):
        super().__init__(parent=parent)
        self.groupID = groupID
        self.videoTrackIndex = videoTrackIndex
        self.labeledVideoTrackIndex = labeledVideoTrackIndex
        self.annotationsTrackIndex = annotationsTrackIndex
        self.partitionsTrackIndex = partitionsTrackIndex
        self.dataTrackIndicies = dataTrackIndicies

    def get_group_id(self):
        return self.groupID

    def get_videoTrackIndex(self):
        return self.videoTrackIndex

    def get_labeledVideoTrackIndex(self):
        return self.labeledVideoTrackIndex

    def get_annotationsTrackIndex(self):
        return self.annotationsTrackIndex

    def get_partitionsTrackIndex(self):
        return self.partitionsTrackIndex

    def get_dataTrackIndicies(self):
        return self.dataTrackIndicies

    def set_videoTrackIndex(self, newValue):
        self.videoTrackIndex = newValue

    def set_labeledVideoTrackIndex(self, newValue):
        self.labeledVideoTrackIndex = newValue

    def set_annotationsTrackIndex(self, newValue):
        self.annotationsTrackIndex = newValue

    def set_partitionsTrackIndex(self, newValue):
        self.partitionsTrackIndex = newValue

    def set_dataTrackIndicies(self, newValue):
        self.dataTrackIndicies = newValue

    def append_dataTrackIndex(self, newValue):
        self.dataTrackIndicies.append(newValue)

    # "has_*_track() functions: test if the group has a specific track type"
    def has_video_track(self):
        return self.get_videoTrackIndex() is not None

    def has_labeledVideo_track(self):
        return self.get_labeledVideoTrackIndex() is not None

    def has_annotations_track(self):
        return self.get_annotationsTrackIndex() is not None

    def has_partitions_track(self):
        return self.get_partitionsTrackIndex() is not None

    # Returns the number of "data" type tracks. Doesn't include partition, annotation, labeled, etc.
    def get_num_data_tracks(self):
        return len(self.get_dataTrackIndicies())

    def has_data_tracks(self):
        return self.get_num_data_tracks() > 0
