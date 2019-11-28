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


# from GUI.Model.TrackConfigs.AbstractTrackConfigs import TrackConfigurationBase, TrackCache, TrackFilterBase

"""
Represents a filter for a specific track
"""
class TrackFilterBase(QObject):

    def __init__(self, trackRecordClass, behavioral_box_ids=None, experiment_ids=None, cohort_ids=None, animal_ids=None, parent=None):
        super(TrackFilterBase, self).__init__(parent=parent)
        self.trackRecordClass = trackRecordClass
        self.behavioral_box_ids = behavioral_box_ids
        self.experiment_ids = experiment_ids
        self.cohort_ids = cohort_ids
        self.animal_ids = animal_ids

    # Returns a filter query so that children classes can extend the filter
    def build_filter_query(self, session):
        query = session.query(self.trackRecordClass)

        if self.behavioral_box_ids is not None:
            query = query.filter(self.trackRecordClass.behavioral_box_id.in_(self.behavioral_box_ids))            
        if self.experiment_ids is not None:
            query = query.filter(self.trackRecordClass.experiment_id.in_(self.experiment_ids))            
        if self.cohort_ids is not None:
            query = query.filter(self.trackRecordClass.cohort_id.in_(self.cohort_ids))            
        if self.animal_ids is not None:
            query = query.filter(self.trackRecordClass.animal_id.in_(self.animal_ids))            

        return query


    # Returns the records. Children classes shouldn't have to override this
    def build_filter(self, session):
        return self.build_filter_query(session).all()


    def __str__(self):
        return 'TrackFilterBase: behavioral_box_ids: {0}, experiment_ids: {1}, cohort_ids: {2}, animal_ids: {3}'.format(self.behavioral_box_ids, self.experiment_ids, self.cohort_ids, self.animal_ids)

    def get_output_dict(self):
        return {'behavioral_box_ids': self.behavioral_box_ids, 'experiment_ids': self.experiment_ids, 'cohort_ids': self.cohort_ids, 'animal_ids': self.animal_ids}

    def get_ids(self):
        return (self.behavioral_box_ids, self.experiment_ids, self.cohort_ids,  self.animal_ids)

    def get_track_record_class(self):
        return self.trackRecordClass


class TrackCache(QObject):
    def __init__(self, modelViewArray=[], parent=None):
        super(TrackCache, self).__init__(parent=parent)
        self.modelViewArray = modelViewArray

    def get_model_view_array(self):
        return self.modelViewArray

    def set_model_view_array(self, newArray):
        self.modelViewArray = newArray


# TrackConfigurationBase: a class that holds the settings for a timeline track
class TrackConfigurationBase(QObject):

    # dataChanged = pyqtSignal()
    # recordsLoaded = pyqtSignal()

    cacheUpdated = pyqtSignal()

    def __init__(self, trackIndex, trackTitle, trackExtendedDescription, trackRecordClass, behavioral_box_ids=None, experiment_ids=None, cohort_ids=None, animal_ids=None, parent=None):
        super(TrackConfigurationBase, self).__init__(parent=parent)
        self.trackIndex = trackIndex
        self.trackTitle = trackTitle
        self.trackExtendedDescription = trackExtendedDescription
        self.filter = TrackFilterBase(trackRecordClass, behavioral_box_ids, experiment_ids, cohort_ids, animal_ids, parent=parent)
        self.cache = TrackCache([], parent=parent)


    def get_track_id(self):
        return self.trackIndex

    def get_track_title(self):
        return self.trackTitle

    def get_track_extended_description(self):
        return self.trackExtendedDescription
    
    def get_track_record_class(self):
        return self.get_filter().get_track_record_class()

    def filter_records(self, session):
        return self.get_filter().build_filter(session)

    # reload(...): called when the filter is changed to update the cache (reloading the records from the database) as needed
    def reload(self, session, owning_parent_track):
        found_records = self.filter_records(session)
        print("track[{0}]: {1} records found".format(self.get_track_id(), len(found_records)))

        # Build the corresponding GUI objects
        built_model_view_container_array = []
        for (index, aRecord) in enumerate(found_records):
            aGuiView = self.get_filter().trackRecordClass.get_gui_view(aRecord, parent=owning_parent_track)
            aModelViewContainer = ModelViewContainer(aRecord, aGuiView)
            built_model_view_container_array.append(aModelViewContainer)

        self.update_cache(built_model_view_container_array)


    # called to update the cache from an external source. Also called internally in self.reload(...)
    def update_cache(self, newCachedModelViewArray):
        self.cache.set_model_view_array(newCachedModelViewArray)
        self.cacheUpdated.emit()

    def get_cache(self):
        return self.cache

    def get_filter(self):
        return self.filter

    def set_filter(self, newFilter):
        self.filter = newFilter

    def __str__(self):
        return 'TrackConfigurationBase: trackIndex: {0}, trackTitle: {1}, trackExtendedDescription: {2}, filter: {3}'.format(self.trackIndex, self.trackTitle, self.trackExtendedDescription, str(self.filter))

