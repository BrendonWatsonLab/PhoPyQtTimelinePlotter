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

"""
Represents a filter for a specific track
"""
class TrackFilter(QObject):
    def __init__(self, behavioral_box_ids, experiment_ids, cohort_ids, animal_ids, allow_original_videos, allow_labeled_videos, parent=None):
        super(TrackFilter, self).__init__(parent=parent)
        self.behavioral_box_ids = behavioral_box_ids
        self.experiment_ids = experiment_ids
        self.cohort_ids = cohort_ids
        self.animal_ids = animal_ids
        self.allow_original_videos = allow_original_videos
        self.allow_labeled_videos = allow_labeled_videos

    def build_filter(self, session):
        if self.allow_original_videos and self.allow_labeled_videos:
            print("Warning: both allow_original_videos and allow_labeled_videos are True!")
            # No filtering needed, we allow any type of videos
            query = session.query(VideoFile)
        elif self.allow_original_videos:
            query = session.query(VideoFile).filter(VideoFile.is_original_video == 1)
        elif self.allow_labeled_videos:
            query = session.query(VideoFile).filter(VideoFile.is_original_video == 0)
        else:
            #both are false
            print("Warning: both allow_original_videos and allow_labeled_videos are False!")
            query = session.query(VideoFile).filter(VideoFile.is_original_video == None)

        if self.behavioral_box_ids is not None:
            query = query.filter(VideoFile.behavioral_box_id.in_(self.behavioral_box_ids))            
        if self.experiment_ids is not None:
            query = query.filter(VideoFile.experiment_id.in_(self.experiment_ids))            
        if self.cohort_ids is not None:
            query = query.filter(VideoFile.cohort_id.in_(self.cohort_ids))            
        if self.animal_ids is not None:
            query = query.filter(VideoFile.animal_id.in_(self.animal_ids))            

        # query = query.filter(VideoFile.behavioral_box_id.in_([1,3]))
        return query.all()


    def __str__(self):
        return 'TrackFilter: behavioral_box_ids: {0}, experiment_ids: {1}, cohort_ids: {2}, animal_ids: {3}, allow_original_videos: {4}, allow_labeled_videos: {5}'.format(self.behavioral_box_ids, self.experiment_ids, self.cohort_ids, self.animal_ids, self.allow_original_videos, self.allow_labeled_videos)

    def get_output_dict(self):
        return {'behavioral_box_ids': self.behavioral_box_ids, 'experiment_ids': self.experiment_ids, 'cohort_ids': self.cohort_ids, 'animal_ids': self.animal_ids, 'allow_original_videos':self.allow_original_videos, 'allow_labeled_videos':self.allow_labeled_videos}


# TrackConfiguration: a class that holds the settings for a timeline track
class TrackConfiguration(QObject):
    def __init__(self, trackIndex, trackTitle, trackExtendedDescription, allow_original_videos, allow_labeled_videos, behavioral_box_ids=None, experiment_ids=None, cohort_ids=None, animal_ids=None, parent=None):
        super(TrackConfiguration, self).__init__(parent=parent)
        self.trackIndex = trackIndex
        self.trackTitle = trackTitle
        self.trackExtendedDescription = trackExtendedDescription
        self.filter = TrackFilter(behavioral_box_ids, experiment_ids, cohort_ids, animal_ids, allow_original_videos, allow_labeled_videos, parent=parent)


    def get_track_id(self):
        return self.trackIndex

    def get_track_title(self):
        return self.trackTitle

    def get_track_extended_description(self):
        return self.trackExtendedDescription
    
    def filter_records(self, session):
        return self.filter.build_filter(session)

    def __str__(self):
        return 'TrackConfiguration: trackIndex: {0}, trackTitle: {1}, trackExtendedDescription: {2}, filter: {3}'.format(self.trackIndex, self.trackTitle, self.trackExtendedDescription, str(self.filter))

