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
            # No filtering needed, we allow any type of videos
            query = session.query(VideoFile)
        elif self.allow_original_videos:
            query = session.query(VideoFile).filter_by(VideoFile.is_original_video == True)
        elif self.allow_labeled_videos:
            query = session.query(VideoFile).filter_by(VideoFile.is_original_video == False)
        else:
            #both are false
            query = session.query(VideoFile).filter_by(VideoFile.is_original_video == None)


        
        if self.behavioral_box_ids is not None:
            result = session.query(VideoFile).filter(VideoFile.behavioral_box_id.in_(self.behavioral_box_ids))            
        if self.experiment_ids is not None:
            result = session.query(VideoFile).filter(VideoFile.experiment_id.in_(self.experiment_ids))            
        if self.cohort_ids is not None:
            result = session.query(VideoFile).filter(VideoFile.cohort_id.in_(self.cohort_ids))            
        if self.animal_ids is not None:
            result = session.query(VideoFile).filter(VideoFile.animal_id.in_(self.animal_ids))            


        result = session.query(VideoFile).filter(VideoFile.behavioral_box_id.in_([1,3]))


    def __str__(self):
        return 'TrackFilter: behavioral_box_id: {0}, experiment_id: {1}, cohort_id: {2}, animal_id: {3}'.format(self.behavioral_box_id, self.experiment_id, self.cohort_id, self.animal_id)

    def get_output_dict(self):
        return {'behavioral_box_id': self.behavioral_box_id, 'experiment_id': self.experiment_id, 'cohort_id': self.cohort_id, 'animal_id': self.animal_id}
