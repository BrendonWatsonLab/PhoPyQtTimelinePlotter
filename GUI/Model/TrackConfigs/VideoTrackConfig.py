#Filters.py
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal

import sqlalchemy as db
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, or_

from app.database.entry_models.DatabaseBase import Base, metadata
from app.database.entry_models.db_model import Animal, BehavioralBox, Context, Experiment, Labjack, Cohort, Subcontext, TimestampedAnnotation, ExperimentalConfigurationEvent, CategoricalDurationLabel, VideoFile
from app.database.entry_models.db_model import StaticFileExtension, FileParentFolder
# from app.database.entry_models.db_model_extension import ExVideoFile

from GUI.Model.ModelViewContainer import ModelViewContainer
from GUI.Model.TrackConfigs.AbstractTrackConfigs import TrackConfigurationBase, TrackCache, TrackFilterBase

"""
Represents a filter for a specific track
"""
class VideoTrackFilter(TrackFilterBase):
    RecordClass = VideoFile

    def __init__(self, allow_original_videos, allow_labeled_videos, behavioral_box_ids=None, experiment_ids=None, cohort_ids=None, animal_ids=None, parent=None):
        super(VideoTrackFilter, self).__init__(behavioral_box_ids, experiment_ids, cohort_ids, animal_ids, parent=parent)
        self.allow_original_videos = allow_original_videos
        self.allow_labeled_videos = allow_labeled_videos

    # Returns a filter query so that children classes can extend the filter
    def build_filter_query(self, session):
        query = super().build_filter_query(session) # Get the parent filter query

        if self.allow_original_videos and self.allow_labeled_videos:
            print("Warning: both allow_original_videos and allow_labeled_videos are True!")
            # No filtering needed, we allow any type of videos
            pass
        elif self.allow_original_videos:
            query = query.filter(type(self).RecordClass.is_original_video == 1)
        elif self.allow_labeled_videos:
            query = query.filter(VideoFile.is_original_video == 0)
        else:
            #both are false
            print("Warning: both allow_original_videos and allow_labeled_videos are False!")
            query = query.filter(type(self).RecordClass.is_original_video == None)
        return query

    def __str__(self):
        return 'VideoTrackFilter: behavioral_box_ids: {0}, experiment_ids: {1}, cohort_ids: {2}, animal_ids: {3}, allow_original_videos: {4}, allow_labeled_videos: {5}'.format(self.behavioral_box_ids, self.experiment_ids, self.cohort_ids, self.animal_ids, self.allow_original_videos, self.allow_labeled_videos)

    def get_output_dict(self):
        return {'behavioral_box_ids': self.behavioral_box_ids, 'experiment_ids': self.experiment_ids, 'cohort_ids': self.cohort_ids, 'animal_ids': self.animal_ids, 'allow_original_videos':self.allow_original_videos, 'allow_labeled_videos':self.allow_labeled_videos}


# VideoTrackConfiguration: a class that holds the settings for a timeline track
class VideoTrackConfiguration(TrackConfigurationBase):

    def __init__(self, trackIndex, trackTitle, trackExtendedDescription, allow_original_videos, allow_labeled_videos, behavioral_box_ids=None, experiment_ids=None, cohort_ids=None, animal_ids=None, parent=None):
        super(VideoTrackConfiguration, self).__init__(trackIndex, trackTitle, trackExtendedDescription, behavioral_box_ids, experiment_ids, cohort_ids, animal_ids, parent=parent)
        self.filter = VideoTrackFilter(allow_original_videos, allow_labeled_videos, behavioral_box_ids, experiment_ids, cohort_ids, animal_ids, parent=parent)

    def __str__(self):
        return 'VideoTrackConfiguration: trackIndex: {0}, trackTitle: {1}, trackExtendedDescription: {2}, filter: {3}'.format(self.trackIndex, self.trackTitle, self.trackExtendedDescription, str(self.filter))

