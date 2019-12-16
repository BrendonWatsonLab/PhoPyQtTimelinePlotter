# -*- coding: utf-8 -*-
import sys
from enum import Enum
from datetime import datetime, timezone, timedelta
from PyQt5.QtWidgets import QFrame
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize

from GUI.Model.TrackGroups import VideoTrackGroupSettings, VideoTrackGroup, TrackReference, TrackChildReference, VideoTrackGroupOwningMixin
from GUI.Model.Errors import SimpleErrorStatusMixin
from GUI.UI.VideoPlayer.VideoPlayerWidget import VideoPlayerWidget

"""
The DataMovieLinkInfo class serves as an intermediate between the data window and the video window. It controls the signals between the two.
Inspired by the C++ DataMoveLinkInfo written by Pho Hale used in neuroscope.

Scope: There can only be one DataMovieLink connected to the main timeline window at a time (as it drives the single video playback red line).
    Also, the video playback timeline in the timeline will only typically intersect a single video at a time (although this isn't strictly true, as one might want to watch the original and the labeled video at the same time)

Ownership:
    This object should then be owned by the timeline?
"""

class DataMovieLink_SyncOption(Enum):
        Bidirectional = 1 # Keep both synced
        VideoToTimeline = 2 #  Set timeline time from video
        TimelineToVideo = 3  # Set video time from timeline




"""
self.videoPlayerWindow: MainVideoPlayerWindow
"""
class DataMovieLinkInfo(SimpleErrorStatusMixin, QObject):

    # videoFileUrlChanged = pyqtSignal(str)

    video_playback_position_changed = pyqtSignal(float) # signal emitted when the video window changes the playback position. Sent to main timeline window

    timeline_datetime_position_changed = pyqtSignal(float) # signal emitted when the timeline changes the playhead position. Sent to video player window.

    # //video_playback_state_changed
    # video_playback_position_updated

    # videoEventChildReference: TrackChildReference

    def __init__(self, videoEventChildReference, videoPlayerWindowRef, mainTimelineWindowRef, parent=None, sync_option=DataMovieLink_SyncOption.Bidirectional):
        super(DataMovieLinkInfo, self).__init__(parent=parent)
        self._error_string = None

        self._videoEventChildReference = videoEventChildReference
        self.videoPlayerWindow = videoPlayerWindowRef
        self.mainTimelineWindowRef = mainTimelineWindowRef

        # TODO: Currently the self.sync_option does nothing. Only video window -> timeline window is currently fully implemented
        self.sync_option = sync_option

        self.active_relative_video_playback_percent_offset = None
        self.active_absolute_datetime = None
        self.active_relative_timeline_percent_offset = None

        # Connect to update self when video window playback position changes
        self.videoPlayerWindow.video_playback_position_updated.connect(self.update_video_playback_position)

        # TODO: Connect to update video playback window when self changes
        # self.videoPlayerWindow.video_playback_position_updated.connect(self.update_video_playback_position)

        self.video_playback_position_changed.connect(self.mainTimelineWindowRef.on_video_playback_position_updated)

        ## TODO NOW: Comment this out if we don't want it.
        # Bound to trigger the video player to update on timeline adjust
        self.timeline_datetime_position_changed.connect(self.videoPlayerWindow.on_timeline_position_updated)



    # Returns the phoDurationEvent_Video type object
    def get_video_duration_event_obj(self):
        return self._videoEventChildReference.get_childEventObject()

    # video window
    def get_video_url(self):
        return self.get_video_duration_event_obj().get_video_url()

    # Getters:
    @property
    def video_url(self):
        return self.get_video_url()

    def get_video_duration(self):
        return self.get_video_duration_event_obj().computeDuration()
    
    def get_video_start_time(self):
        return self.get_video_duration_event_obj().startTime

    def get_video_end_time(self):
        return self.get_video_duration_event_obj().endTime

    # timeline window
    def get_timeline_duration(self):
        return self.mainTimelineWindowRef.totalDuration
    
    def get_timeline_start_time(self):
        return self.mainTimelineWindowRef.totalStartTime

    def get_timeline_end_time(self):
        return self.mainTimelineWindowRef.totalEndTime       


    # Active variables
    def get_active_absolute_datetime(self):
        return self.active_absolute_datetime
    
    def get_active_relative_video_playback_percent_offset(self):
        return self.active_relative_video_playback_percent_offset

    def get_active_relative_timeline_percent_offset(self):
        return self.active_relative_timeline_percent_offset


    # Given a video playback duration % (0.0 - 1.0), returns the real-world absolute time corresponding to it
    def compute_absolute_time(self, video_duration_percent):
        video_duration_relative_offset = video_duration_percent * self.get_video_duration()
        return self.get_video_duration_event_obj().compute_absolute_time(video_duration_relative_offset)


    # Given a real-world absolute datetime, return the video playback duration % (0.0 - 1.0) corresponding to it
    def compute_video_percent_offset(self, absolute_time):
        # check if absolute_time is within the video
        if (not self.get_video_duration_event_obj().contains(absolute_time)):
            return None
        else:
            video_duration_relative_offset = self.get_video_duration_event_obj().compute_relative_offset_duration(absolute_time)
            return (video_duration_relative_offset / self.get_video_duration())


    # Returns the percent offset of the absolute_time in the current timeline
    def compute_timeline_percent_offset(self, absolute_time):
        # check if absolute_time is within the timeline
        if (not self.mainTimelineWindowRef.contains_date(absolute_time)):
            return None
        else:
            timeline_duration_relative_offset = self.mainTimelineWindowRef.compute_relative_offset_duration(absolute_time)
            return (timeline_duration_relative_offset / self.get_timeline_duration())





    # update_video_playback_position(...): called from the video player window's slider updated event
    @pyqtSlot(float)
    def update_video_playback_position(self, updatedRelativePercentVideoPlaybackPosition):
        self.active_relative_video_playback_percent_offset = updatedRelativePercentVideoPlaybackPosition
        self.active_absolute_datetime = self.compute_absolute_time(updatedRelativePercentVideoPlaybackPosition)
        self.active_relative_timeline_percent_offset = self.compute_timeline_percent_offset(self.active_absolute_datetime)
        # self.video_playback_position_changed.emit(absolute_datetime)
        self.video_playback_position_changed.emit(self.active_relative_timeline_percent_offset)


    # update_timeline_playhead_position(...): called from the main timeline window when the playhead is updated
    @pyqtSlot(datetime)
    def update_timeline_playhead_position(self, updatedDatetime):
        self.active_absolute_datetime = updatedDatetime
        self.active_relative_video_playback_percent_offset = self.compute_video_percent_offset(self.active_absolute_datetime)
        self.timeline_datetime_position_changed.emit( self.active_relative_video_playback_percent_offset)




    
"""
Informs that the starting time and/or the timeWindow have changed.
  * @param startTime starting time.
  * @param timeWindow time window.
"""