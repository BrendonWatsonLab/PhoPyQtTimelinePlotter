# -*- coding: utf-8 -*-
import sys
from enum import Enum
from datetime import datetime, timezone, timedelta
from PyQt5.QtWidgets import QFrame
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize


"""
The DataMovieLinkInfo class serves as an intermediate between the data window and the video window. It controls the signals between the two.
Inspired by the C++ DataMoveLinkInfo written by Pho Hale used in neuroscope.
"""

class DataMovieLink_SyncOption(Enum):
        Bidirectional = 1 # Keep both synced
        VideoToTimeline = 2 #  Set timeline time from video
        TimelineToVideo = 3  # Set video time from timeline

"""
self.videoDurationEventObj: phoDurationEvent_Video
self.videoPlayerWindow: MainVideoPlayerWindow
"""
class DataMovieLinkInfo(QObject):

    # videoFileUrlChanged = pyqtSignal(str)

    video_playback_position_changed = pyqtSignal(float) # signal emitted when the video window changes the playback position. Sent to main timeline window

    timeline_datetime_position_changed = pyqtSignal(float) # signal emitted when the timeline changes the playhead position. Sent to video player window.


    # //video_playback_state_changed
    # video_playback_position_updated

    def __init__(self, videoEventObj, videoPlayerWindowRef, mainTimelineWindowRef, parent=None, sync_option=DataMovieLink_SyncOption.Bidirectional):
        super(DataMovieLinkInfo, self).__init__(parent=parent)
        self.videoDurationEventObj = videoEventObj
        self.videoPlayerWindow = videoPlayerWindowRef
        self.mainTimelineWindowRef = mainTimelineWindowRef

        # TODO: Currently the self.sync_option does nothing. Only video window -> timeline window is currently fully implemented
        self.sync_option = sync_option

        # Connect to update self when video window playback position changes
        self.videoPlayerWindow.video_playback_position_updated.connect(self.update_video_playback_position)

        # TODO: Connect to update video playback window when self changes
        # self.videoPlayerWindow.video_playback_position_updated.connect(self.update_video_playback_position)

        self.video_playback_position_changed.connect(self.mainTimelineWindowRef.on_video_playback_position_updated)

        ## TODO NOW: Comment this out if we don't want it.
        # Bound to trigger the video player to update on timeline adjust
        self.timeline_datetime_position_changed.connect(self.videoPlayerWindow.on_timeline_position_updated)


    # video window
    def get_video_url(self):
        return self.videoDurationEventObj.get_video_url()

    def get_video_duration(self):
        return self.videoDurationEventObj.computeDuration()
    
    def get_video_start_time(self):
        return self.videoDurationEventObj.startTime

    def get_video_end_time(self):
        return self.videoDurationEventObj.endTime

    # timeline window
    def get_timeline_duration(self):
        return self.mainTimelineWindowRef.totalDuration
    
    def get_timeline_start_time(self):
        return self.mainTimelineWindowRef.totalStartTime

    def get_timeline_end_time(self):
        return self.mainTimelineWindowRef.totalEndTime       


    # Given a video playback duration % (0.0 - 1.0), returns the real-world absolute time corresponding to it
    def compute_absolute_time(self, video_duration_percent):
        video_duration_relative_offset = video_duration_percent * self.get_video_duration()
        return self.videoDurationEventObj.compute_absolute_time(video_duration_relative_offset)


    # Given a real-world absolute datetime, return the video playback duration % (0.0 - 1.0) corresponding to it
    def compute_video_percent_offset(self, absolute_time):
        # check if absolute_time is within the video
        if (not self.videoDurationEventObj.contains(absolute_time)):
            return None
        else:
            video_duration_relative_offset = self.videoDurationEventObj.compute_relative_offset_duration(absolute_time)
            return (video_duration_relative_offset / self.get_video_duration())


    # Returns the percent offset of the absolute_time in the current timeline
    def compute_timeline_percent_offset(self, absolute_time):
        # check if absolute_time is within the timeline
        if (not self.mainTimelineWindowRef.contains_date(absolute_time)):
            return None
        else:
            timeline_duration_relative_offset = self.mainTimelineWindowRef.compute_relative_offset_duration(absolute_time)
            return (timeline_duration_relative_offset / self.get_timeline_duration())


    def compute_absolute_time(self, video_duration_percent):
        video_duration_relative_offset = video_duration_percent * self.get_video_duration()
        return self.videoDurationEventObj.compute_absolute_time(video_duration_relative_offset)




    # update_video_playback_position(...): called from the video player window's slider updated event
    @pyqtSlot(float)
    def update_video_playback_position(self, updatedRelativePercentVideoPlaybackPosition):
        absolute_datetime = self.compute_absolute_time(updatedRelativePercentVideoPlaybackPosition)
        relative_timeline_percent_offset = self.compute_timeline_percent_offset(absolute_datetime)
        # self.video_playback_position_changed.emit(absolute_datetime)
        self.video_playback_position_changed.emit(relative_timeline_percent_offset)


    # update_timeline_playhead_position(...): called from the main timeline window when the playhead is updated
    @pyqtSlot(datetime)
    def update_timeline_playhead_position(self, updatedDatetime):
        video_percent_offset = self.compute_video_percent_offset(updatedDatetime)
        self.timeline_datetime_position_changed.emit(video_percent_offset)



    # @pyqtSlot(str)
    # def set_video_url(self, url):
    #     self.video_file_url = url



# class DataMovieLinkInfo(QObject):

#     videoFileUrlChanged = pyqtSignal(str)


#     def __init__(self, video_file_url, parent=None, sync_option=DataMovieLink_SyncOption.Bidirectional):
#         super(DataMovieLinkInfo, self).__init__(parent=parent)
#         self.video_file_url = video_file_url
#         self.sync_option = sync_option
#         self.video_duration =

#     def get_video_url(self):
#         return self.video_file_url

#     @pyqtSlot(str)
#     def set_video_url(self, url):
#         self.video_file_url = url

    
"""
Informs that the starting time and/or the timeWindow have changed.
  * @param startTime starting time.
  * @param timeWindow time window.
"""