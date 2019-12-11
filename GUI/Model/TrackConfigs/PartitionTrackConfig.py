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
from GUI.Model.TrackType import TrackType

# INCLUDES:
# from GUI.Model.TrackConfigs.PartitionTrackConfig import PartitionTrackFilter, PartitionTrackConfiguration

"""
Represents a filter for a specific track
"""
class PartitionTrackFilter(TrackFilterBase):

    def __init__(self, contextConfigObject, behavioral_box_ids=None, experiment_ids=None, cohort_ids=None, animal_ids=None, parent=None):
        super(PartitionTrackFilter, self).__init__(CategoricalDurationLabel, behavioral_box_ids, experiment_ids, cohort_ids, animal_ids, parent=parent)
        self.contextConfigObject = contextConfigObject

    # Returns a filter query so that children classes can extend the filter
    def build_filter_query(self, session):
        query = super().build_filter_query(session) # Get the parent filter query
        
        if self.contextConfigObject is not None:
            currSearchSubcontext = self.contextConfigObject.get_subcontext()
            if currSearchSubcontext is not None:
                # add the filter to the query that the subcontext must match the object's subcontext
                query = query.filter(CategoricalDurationLabel.Subcontext==currSearchSubcontext)
                pass
            else:
                print("Warning: PartitionTrackFilter's self.contextConfigObject.get_subcontext() is None! Permitting all contexts/subcontexts.")
                pass
        else:
            print("Warning: PartitionTrackFilter's self.contextConfigObject is None! Permitting all contexts/subcontexts.")
            pass

        return query

    def __str__(self):
        return 'PartitionTrackFilter: behavioral_box_ids: {0}, experiment_ids: {1}, cohort_ids: {2}, animal_ids: {3}, contextConfigObject: {4}'.format(self._get_behavioral_box_ids_str(), self._get_experiment_ids_str(), self._get_cohort_ids_str(), self._get_animal_ids_str(), str(self.contextConfigObject))

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


# PartitionTrackConfiguration: a class that holds the settings for a timeline track
class PartitionTrackConfiguration(TrackConfigurationBase):

    def __init__(self, trackIndex, trackTitle, trackExtendedDescription, contextConfigObject, behavioral_box_ids=None, experiment_ids=None, cohort_ids=None, animal_ids=None, parent=None):
        super(PartitionTrackConfiguration, self).__init__(trackIndex, trackTitle, trackExtendedDescription, CategoricalDurationLabel, behavioral_box_ids, experiment_ids, cohort_ids, animal_ids, parent=parent)
        self.filter = PartitionTrackFilter(contextConfigObject, behavioral_box_ids, experiment_ids, cohort_ids, animal_ids, parent=parent)

    def __str__(self):
        return 'PartitionTrackConfiguration: trackIndex: {0}, trackTitle: {1}, trackExtendedDescription: {2}, filter: {3}'.format(self.trackIndex, self.trackTitle, self.trackExtendedDescription, str(self.filter))

