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


class DataMovieLinkInfo(QObject):

    videoFileUrlChanged = pyqtSignal(str)


    def __init__(self, video_file_url, parent=None, sync_option=DataMovieLink_SyncOption.Bidirectional):
        super(DataMovieLinkInfo, self).__init__(parent=parent)
        self.video_file_url = video_file_url
        self.sync_option = sync_option

    def get_video_url(self):
        return self.video_file_url

    @pyqtSlot(str)
    def set_video_url(self, url):
        self.video_file_url = url

    
"""
Informs that the starting time and/or the timeWindow have changed.
  * @param startTime starting time.
  * @param timeWindow time window.
"""