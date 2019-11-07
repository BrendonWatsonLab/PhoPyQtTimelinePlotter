import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

"""
Represents a experiment instance
"""
class ExperimentContextInfo(QObject):
    def __init__(self, database_record_id, experiment_id, cohort_id, animal_id, notes='', extended_data=dict()):
        super(ExperimentContextInfo, self).__init__(None)
        self.database_record_id = database_record_id
        self.experiment_id = experiment_id
        self.cohort_id = cohort_id
        self.animal_id = animal_id
        self.notes = notes
        self.extended_data = extended_data

    def __eq__(self, otherEvent):
        #return self.database_record_id == otherEvent.database_record_id and self.experiment_id == otherEvent.experiment_id and self.cohort_id == otherEvent.cohort_id and self.animal_id == otherEvent.animal_id
        return self.database_record_id == otherEvent.database_record_id

    # Less Than (<) operator
    def __lt__(self, otherEvent):
        return self.database_record_id < otherEvent.database_record_id

    def __str__(self):
        return 'ExperimentContextInfo[{0}]: experiment_id: {1}, cohort_id: {2}, animal_id: {3}, notes: {4}, other: {5}'.format(self.database_record_id, self.experiment_id, self.cohort_id, self.animal_id, self.notes, str(self.extended_data))


"""
Represents a Video File
"""
class VideoInfo(QObject):
    def __init__(self, fullName, baseName, fileExtension, fullParentPath, startTime, endTime, duration, is_original_video, experimentContextInfo, extended_data=dict()):
        super(VideoInfo, self).__init__(None)
        self.fullName = fullName
        self.baseName = baseName
        self.fileExtension = fileExtension
        self.fullParentPath = fullParentPath
        self.startTime = startTime
        self.endTime = endTime
        self.duration = duration
        self.is_original_video = is_original_video
        self.experimentContextInfo = experimentContextInfo
        self.extended_data = extended_data

    def __eq__(self, otherEvent):
        return self.fullParentPath == otherEvent.fullParentPath and self.fullName == otherEvent.fullName
    
    # Returns true if it's the same video just in a different format or path. Not based on the baseName itself, but instead on its parsed/extracted content, allowing for multiple naming conventions.
    # Also recognizes the DeepLabCut labeled video versions as the same as the base video
    def is_same_video_content(self, otherEvent):
        return self.startTime == otherEvent.startTime and self.endTime == otherEvent.endTime and self.experimentContextInfo == otherEvent.experimentContextInfo

    # Returns true if it's the original video as opposed to a pre-processed or labeled version
    def is_original_video(self):
        return True

    # Less Than (<) operator
    def __lt__(self, otherEvent):
        return self.startTime < otherEvent.startTime

    def __str__(self):
        return 'Video Info: fullParentPath: {0}, fullName: {1}, startTime: {2}, duration {3}'.format(self.fullParentPath, self.fullName, self.startTime, self.duration)
