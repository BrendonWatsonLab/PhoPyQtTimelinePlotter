import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

"""
Represents a experiment instance
"""
class ExperimentContextInfo(QObject):
    def __init__(self, database_record_id, behavioral_box_id, experiment_id, cohort_id, animal_id, notes='', extended_data=dict()):
        super(ExperimentContextInfo, self).__init__(None)
        self.database_record_id = database_record_id
        self.behavioral_box_id = behavioral_box_id
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
        return 'ExperimentContextInfo[{0}]: behavioral_box_id: {1}, experiment_id: {2}, cohort_id: {3}, animal_id: {4}, notes: {5}, other: {6}'.format(self.database_record_id, self.behavioral_box_id, self.experiment_id, self.cohort_id, self.animal_id, self.notes, str(self.extended_data))

    def get_output_dict(self):
        return {'behavioral_box_id': self.behavioral_box_id, 'experiment_id': self.experiment_id, 'cohort_id': self.cohort_id, 'animal_id': self.animal_id, 'notes': self.notes }

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
        self.is_original_video = is_original_video # true if it's the original video as opposed to a pre-processed or labeled version
        self.experimentContextInfo = experimentContextInfo
        self.extended_data = extended_data

    def __eq__(self, otherEvent):
        return self.fullParentPath == otherEvent.fullParentPath and self.fullName == otherEvent.fullName
    
    # Returns true if it's the same video just in a different format or path. Not based on the baseName itself, but instead on its parsed/extracted content, allowing for multiple naming conventions.
    # Also recognizes the DeepLabCut labeled video versions as the same as the base video
    def is_same_video_content(self, otherEvent):
        return self.startTime == otherEvent.startTime and self.endTime == otherEvent.endTime and self.experimentContextInfo == otherEvent.experimentContextInfo

    # Less Than (<) operator
    def __lt__(self, otherEvent):
        return self.startTime < otherEvent.startTime

    def __str__(self):
        return 'Video Info: fullParentPath: {0}, fullName: {1}, startTime: {2}, duration {3}'.format(self.fullParentPath, self.fullName, self.startTime, self.duration)

    def get_output_dict(self):
        return {'base_name': self.baseName, 'file_fullname': self.fullName, 'file_extension': self.fileExtension,
        'parent_path': self.fullParentPath, 'path': self.get_full_path(),
        'parsed_date': self.startTime, 'computed_end_date': self.endTime, 'is_deeplabcut_labeled_video': self.get_is_deeplabcut_labeled_video(),
        'properties': self.get_properties_dict(), 'extended_properties': self.get_extended_properties_dict()}

    def get_properties_dict(self):
        return {'duration': self.duration}

    def get_extended_properties_dict(self):
        # return {'behavioral_box_id': self.experimentContextInfo}
        return self.experimentContextInfo.get_output_dict()

    def get_is_deeplabcut_labeled_video(self):
        if (self.is_original_video is None):
            return None
        else:
            return (not self.is_original_video)

    def get_full_path(self):
        entries = Path(self.fullParentPath)
        return entries.joinpath(self.fullName).resolve(strict=True)