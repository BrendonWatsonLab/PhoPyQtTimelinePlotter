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

from GUI.Model.TrackType import TrackType, TrackStorageArray

# INCLUDE:
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

    # Returns the records. Children classes shouldn't have to override this unless they want to sort it differently
    def build_filter(self, session):
        return self.build_filter_query(session).all()

    def _get_behavioral_box_ids_str(self, noneString="Any", array_opening_bracket = "[", array_closing_bracket = "]", enable_single_element_arrays = False):
        out_string = ""
        if self.behavioral_box_ids is None:
            return noneString
        else:
            currArray = self.behavioral_box_ids
            if (enable_single_element_arrays or (len(currArray)>1)):
                out_string = out_string + array_opening_bracket
            for aBBID in currArray:
                out_string = out_string + "B{0:02}".format(aBBID-1)
            if (enable_single_element_arrays or (len(currArray)>1)):
                out_string = out_string + array_closing_bracket
            return out_string

    def _get_experiment_ids_str(self, noneString="Any", array_opening_bracket = "[", array_closing_bracket = "]", enable_single_element_arrays = False):
        out_string = ""
        if self.experiment_ids is None:
            return noneString
        else:
            currArray = self.experiment_ids
            if (enable_single_element_arrays or (len(currArray)>1)):
                out_string = out_string + array_opening_bracket
            for anID in self.experiment_ids:
                out_string = out_string + "E{0:04}".format(anID-1)
            if (enable_single_element_arrays or (len(currArray)>1)):
                out_string = out_string + array_closing_bracket
            return out_string

    def _get_cohort_ids_str(self, noneString="Any", array_opening_bracket = "[", array_closing_bracket = "]", enable_single_element_arrays = False):
        out_string = ""
        if self.cohort_ids is None:
            return noneString
        else:
            currArray = self.cohort_ids
            if (enable_single_element_arrays or (len(currArray)>1)):
                out_string = out_string + array_opening_bracket
            for anID in self.cohort_ids:
                out_string = out_string + "C{0:04}".format(anID-1)
            if (enable_single_element_arrays or (len(currArray)>1)):
                out_string = out_string + array_closing_bracket
            return out_string

    def _get_animal_ids_str(self, noneString="Any", array_opening_bracket = "[", array_closing_bracket = "]", enable_single_element_arrays = False):
        out_string = ""
        if self.animal_ids is None:
            return noneString
        else:
            currArray = self.animal_ids
            if (enable_single_element_arrays or (len(currArray)>1)):
                out_string = out_string + array_opening_bracket
            for anID in self.animal_ids:
                out_string = out_string + "A{0:04}".format(anID-1)
            if (enable_single_element_arrays or (len(currArray)>1)):
                out_string = out_string + array_closing_bracket
            return out_string


    def __str__(self):
        # return 'TrackFilterBase: behavioral_box_ids: {0}, experiment_ids: {1}, cohort_ids: {2}, animal_ids: {3}'.format(self.behavioral_box_ids, self.experiment_ids, self.cohort_ids, self.animal_ids)
        return 'TrackFilterBase: behavioral_box_ids: {0}, experiment_ids: {1}, cohort_ids: {2}, animal_ids: {3}'.format(self._get_behavioral_box_ids_str(), self._get_experiment_ids_str(), self._get_cohort_ids_str(), self._get_animal_ids_str())

    def get_selection_string(self):
        out_string = ""
        array_opening_bracket = "["
        array_closing_bracket = "]"
        enable_single_element_arrays = False
        show_track_type = True

        if show_track_type:
            currType = self.get_track_type()
            out_string = out_string + currType.get_medium_str()
            out_string = out_string + ":"
            
        if self.behavioral_box_ids is not None:
            out_string = out_string + self._get_behavioral_box_ids_str("", array_opening_bracket=array_opening_bracket, array_closing_bracket=array_closing_bracket, enable_single_element_arrays=enable_single_element_arrays)

        if self.experiment_ids is not None:
            out_string = out_string + self._get_experiment_ids_str("", array_opening_bracket=array_opening_bracket, array_closing_bracket=array_closing_bracket, enable_single_element_arrays=enable_single_element_arrays)

        if self.cohort_ids is not None:
            out_string = out_string + self._get_cohort_ids_str("", array_opening_bracket=array_opening_bracket, array_closing_bracket=array_closing_bracket, enable_single_element_arrays=enable_single_element_arrays)

        if self.animal_ids is not None:
            out_string = out_string + self._get_animal_ids_str("", array_opening_bracket=array_opening_bracket, array_closing_bracket=array_closing_bracket, enable_single_element_arrays=enable_single_element_arrays)

        return out_string

    def get_output_dict(self):
        return {'behavioral_box_ids': self.behavioral_box_ids, 'experiment_ids': self.experiment_ids, 'cohort_ids': self.cohort_ids, 'animal_ids': self.animal_ids}

    def get_ids(self):
        return (self.behavioral_box_ids, self.experiment_ids, self.cohort_ids,  self.animal_ids)

    def get_track_record_class(self):
        return self.trackRecordClass

    # get_track_type(): returns GUI.Model.TrackType type object
    def get_track_type(self):
        return self.get_track_record_class().get_track_type()

    # get_track_storageArray_type(): returns GUI.Model.TrackStorageArray type object
    def get_track_storageArray_type(self):
        return self.get_track_type().get_storage_array_type()


    # matches(other_filter): returns True IFF behavioral_box_ids, experiment_ids, cohort_ids, and animal_ids all match other_filter
    def matches(self, other_filter):
        return ((self.behavioral_box_ids == other_filter.behavioral_box_ids) and (self.experiment_ids == other_filter.experiment_ids) and (self.cohort_ids == other_filter.cohort_ids) and (self.animal_ids == other_filter.animal_ids))


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
        # self.trackType = trackRecordClass.get_track_type()

        self.filter = TrackFilterBase(trackRecordClass, behavioral_box_ids, experiment_ids, cohort_ids, animal_ids, parent=parent)
        self.cache = TrackCache([], parent=parent)

    # get_should_auto_build_gui_views(): true if the gui views should automatically be built from the records after a reload(...) command
    # can be overriden by children if we don't want the GUI views auto-built
    def get_should_auto_build_gui_views(self):
        return True

    def get_track_id(self):
        return self.trackIndex

    def get_track_title(self):
        return self.trackTitle

    def get_track_extended_description(self):
        return self.trackExtendedDescription
    
    def get_track_record_class(self):
        return self.get_filter().get_track_record_class()

    # get_track_type(): returns GUI.Model.TrackType type object
    def get_track_type(self):
        return self.get_filter().get_track_type()

    # get_track_storageArray_type(): returns GUI.Model.TrackStorageArray type object
    def get_track_storageArray_type(self):
        return self.get_filter().get_track_storageArray_type()

    def filter_records(self, session):
        return self.get_filter().build_filter(session)

    # reload(...): called when the filter is changed to update the cache (reloading the records from the database) as needed
    def reload(self, session, owning_parent_track):
        found_records = self.filter_records(session)
        print("track[{0}]: {1} records found".format(self.get_track_id(), len(found_records)))

        # Build the corresponding GUI objects
        built_model_view_container_array = []
        for (index, aRecord) in enumerate(found_records):
            aGuiView = None
            if self.get_should_auto_build_gui_views():
                aGuiView = self.get_filter().trackRecordClass.get_gui_view(aRecord, parent=owning_parent_track)
            else:
                aGuiView = None

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


    # update_labels_dynamically(): updates the labels dynamically from the active filter
    def update_labels_dynamically(self):
        self.trackTitle = self.get_filter().get_selection_string()
        self.trackExtendedDescription = self.get_filter().get_selection_string()
        return