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

# from app.database.entry_models.DatabaseBase import Base, metadata
# from app.database.entry_models.db_model import Animal, BehavioralBox, Context, Experiment, Labjack, Cohort, Subcontext, TimestampedAnnotation, ExperimentalConfigurationEvent, CategoricalDurationLabel, VideoFile
# from app.database.entry_models.db_model import StaticFileExtension, FileParentFolder
# from app.database.entry_models.db_model_extension import ExVideoFile

from app.filesystem.FilesystemRecordBase import *

from GUI.Model.ModelViewContainer import ModelViewContainer
from GUI.Model.TrackConfigs.AbstractTrackConfigs import TrackConfigurationBase, TrackCache, TrackFilterBase
from GUI.Model.TrackType import TrackType

# INCLUDES:
# from GUI.Model.TrackConfigs.DataFileTrackConfig import DataFileTrackFilterConfig, DataFileTrackConfiguration

"""
Represents a filter for a specific track
"""
class DataFileTrackFilterConfig(TrackFilterBase):

    def __init__(self, contextConfigObject, behavioral_box_ids=None, experiment_ids=None, cohort_ids=None, animal_ids=None, parent=None):
        super(DataFileTrackFilterConfig, self).__init__(FilesystemRecordBase, behavioral_box_ids, experiment_ids, cohort_ids, animal_ids, parent=parent)
        self.contextConfigObject = contextConfigObject

    # Returns a filter query so that children classes can extend the filter
    def build_filter_query(self, session):
        print("ERROR: SHOULDN'T BE CALLING DataFileTrackConfig.build_filter_query(...)!!!")
        return None



    # Returns the records sorted by the start_date field
    def build_filter(self, session):
        return self.build_filter_query(session).order_by(FilesystemRecordBase.start_date).all()


    def __str__(self):
        return 'DataFileTrackConfig: behavioral_box_ids: {0}, experiment_ids: {1}, cohort_ids: {2}, animal_ids: {3}, contextConfigObject: {4}'.format(self._get_behavioral_box_ids_str(), self._get_experiment_ids_str(), self._get_cohort_ids_str(), self._get_animal_ids_str(), str(self.contextConfigObject))

    def get_selection_string(self):
        out_string = super().get_selection_string()
        if self.contextConfigObject is not None:
            out_string = out_string + ", "
            out_string = out_string + str(self.contextConfigObject)
        else:
            out_string = out_string + ", No Context"
        return out_string

    def get_output_dict(self):
        return {'behavioral_box_ids': self.behavioral_box_ids, 'experiment_ids': self.experiment_ids, 'cohort_ids': self.cohort_ids, 'animal_ids': self.animal_ids, 'contextConfigObject':self.contextConfigObject}


# DataFileTrackConfiguration: a class that holds the settings for a timeline track
class DataFileTrackConfiguration(TrackConfigurationBase):

    def __init__(self, trackIndex, trackTitle, trackExtendedDescription, behavioral_box_ids=None, experiment_ids=None, cohort_ids=None, animal_ids=None, parent=None):
        super(DataFileTrackConfiguration, self).__init__(trackIndex, trackTitle, trackExtendedDescription, FilesystemRecordBase, behavioral_box_ids, experiment_ids, cohort_ids, animal_ids, parent=parent)
        self.filter = DataFileTrackFilterConfig(contextConfigObject, behavioral_box_ids, experiment_ids, cohort_ids, animal_ids, parent=parent)

    # get_should_auto_build_gui_views(): true if the gui views should automatically be built from the records after a reload(...) command
    # can be overriden by children if we don't want the GUI views auto-built
    def get_should_auto_build_gui_views(self):
        return False

    def __str__(self):
        return 'DataFileTrackConfiguration: trackIndex: {0}, trackTitle: {1}, trackExtendedDescription: {2}, filter: {3}'.format(self.trackIndex, self.trackTitle, self.trackExtendedDescription, str(self.filter))

