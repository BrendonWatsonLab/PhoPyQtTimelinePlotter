# -*- coding: utf-8 -*-
import sys
from enum import Enum
from datetime import datetime, timezone, timedelta
from PyQt5.QtWidgets import QFrame, QDialog, QFrame, QLabel, QHBoxLayout
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize

from GUI.Model.TrackGroups import VideoTrackGroupSettings, VideoTrackGroup, TrackReference, TrackChildReference, VideoTrackGroupOwningMixin
from GUI.Model.Errors import SimpleErrorStatusMixin
from GUI.Windows.VideoPlayer.VideoPlayerWidget import VideoPlayerWidget

from app.filesystem.VideoPreviewThumbnailGeneratingMixin import VideoThumbnail, VideoPreviewThumbnailGenerator

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

    # Thumbnail Generation signals
    thumbnail_generated = pyqtSignal(VideoThumbnail) # (thumbnailObj: VideoThumbnail)
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

        # Video Thumbnail Generator:
        self.video_thumbnail_popover_window = None
        self.videoThumbnailGenerator = VideoPreviewThumbnailGenerator([], parent=self)
        # self.videoThumbnailGenerator.thumbnailGenerationComplete.connect(self.on_all_videos_thumbnail_generation_complete)
        self.videoThumbnailGenerator.videoThumbnailGenerationComplete.connect(self.on_video_event_thumbnail_generation_complete) # Single video file
        self.videoThumbnailGenerator.videoFrameThumbnailsUpdated.connect(self.on_cache_frame_thumbnails_updated) # Single frame of a signle video file
        # Connect signal to the video player window
        self.thumbnail_generated.connect(self.videoPlayerWindow.on_video_thumbnail_generated)

        self.initially_generate_thumbnails()


    # TODO: Thumbnail generation
    def initially_generate_thumbnails(self):
        proposed_video_file_path = self.get_video_url()
        if (proposed_video_file_path is not None):
            # Have a valid video file path
            print("TimelineDrawingWindow.on_video_track_child_generate_thumbnails(...): starting thumbnail generation with video: {0}...".format(str(proposed_video_file_path)))
            # register the video duration object as a receiver of the thumbnail generation finished event
            # self.get_video_thumbnail_generator().videoThumbnailGenerationComplete.connect(videoDurationObj.on_thumbnails_loaded)

            # Start thumbnail generation for this video file too:
            self.get_video_thumbnail_generator().add_video_path(str(proposed_video_file_path))

    def generate_thumbnails(self, desired_frame_indicies):
        proposed_video_file_path = self.get_video_url()
        if (proposed_video_file_path is not None):
            self.get_video_thumbnail_generator().reload_data([str(proposed_video_file_path)], desired_frame_indicies)
        else:
            print("WARNING: generate_thumbnails(...) called but video path is invalid!")

    # Returns the TrackChildReference reference type object
    def get_video_event_reference(self):
        return self._videoEventChildReference


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


    ## Video Thumbnail Generation
    def get_video_thumbnail_generator(self):
        return self.videoThumbnailGenerator

    # Called by the cache's update_frame_thumbnail_results(...) function to indicate that a thumbnail has been generated for a given frame
    @pyqtSlot(str, VideoThumbnail)
    def on_cache_frame_thumbnails_updated(self, videoFileName, videoThumbnailResultObj):
        if videoFileName != str(self.get_video_url()):
            # Doesn't match this video file
            print("WARNING: name doesn't match! (updated result video filename: {0}, target video file name: {1}".format(str(videoFileName), str(self.get_video_url())))
            return

        # Just re-emit the signal
        self.thumbnail_generated.emit(videoThumbnailResultObj)



    # on_video_event_thumbnail_generation_complete(): Called when a thumbnail generation is complete for a given video
    @pyqtSlot(str, list)
    def on_video_event_thumbnail_generation_complete(self, videoFileName, generated_thumbnails_list):
        print("DataMovieLinkInfo.on_video_event_thumbnail_generation_complete(videoFileName: {0})...".format(str(videoFileName)))
        # self.video_thumbnail_popover_window = QDialog(self)
        # # self.video_thumbnail_popover_window.setCentr
        # # A vertical box layout
        # # thumbnailsLayout = QVBoxLayout()
        # thumbnailsLayout = QHBoxLayout()

        # # desiredThumbnailSizeKey = "40"
        # desiredThumbnailSizeKey = "160"

        # # for (aSearchPathIndex, aSearchPath) in enumerate(self.searchPaths):
        # for (key_path, cache_value) in self.get_video_thumbnail_generator().get_cache().items():
        #     # key_path: the video file path that had the thumbnails generated for it
        #     print("thumbnail generation complete for [{0}]: {1} frames".format(str(key_path), len(cache_value)))
        #     for (index, aVideoThumbnailObj) in enumerate(cache_value):
        #         currThumbsDict = aVideoThumbnailObj.get_thumbs_dict()
        #         # currThumbnailImage: should be a QImage
        #         currThumbnailImage = currThumbsDict[desiredThumbnailSizeKey]
        #         w = QLabel()
        #         w.setPixmap(QPixmap.fromImage(currThumbnailImage))
        #         thumbnailsLayout.addWidget(w)

        # self.video_thumbnail_popover_window.setLayout(thumbnailsLayout)
        # self.video_thumbnail_popover_window.show()

        # self.update()

    # on_video_thumbnail_generation_complete(): Called when a thumbnail generation is complete for a given video
    @pyqtSlot()
    def on_all_videos_thumbnail_generation_complete(self):
        print("DataMovieLinkInfo.on_all_videos_thumbnail_generation_complete()...")
        # self.video_thumbnail_popover_window = QDialog(self)
        # # self.video_thumbnail_popover_window.setCentr
        # # A vertical box layout
        # thumbnailsLayout = QVBoxLayout()

        # # desiredThumbnailSizeKey = "40"
        # desiredThumbnailSizeKey = "160"

        # # for (aSearchPathIndex, aSearchPath) in enumerate(self.searchPaths):
        # for (key_path, cache_value) in self.get_video_thumbnail_generator().get_cache().items():
        #     # key_path: the video file path that had the thumbnails generated for it
        #     print("thumbnail generation complete for [{0}]: {1} frames".format(str(key_path), len(cache_value)))
        #     for (index, aVideoThumbnailObj) in enumerate(cache_value):
        #         currThumbsDict = aVideoThumbnailObj.get_thumbs_dict()
        #         # currThumbnailImage: should be a QImage
        #         currThumbnailImage = currThumbsDict[desiredThumbnailSizeKey]
        #         w = QLabel()
        #         w.setPixmap(QtGui.QPixmap.fromImage(currThumbnailImage))
        #         thumbnailsLayout.addWidget(w)

        # self.video_thumbnail_popover_window.setLayout(thumbnailsLayout)
        # self.video_thumbnail_popover_window.show()

        # self.update()
    
    
"""
Informs that the starting time and/or the timeWindow have changed.
  * @param startTime starting time.
  * @param timeWindow time window.
"""