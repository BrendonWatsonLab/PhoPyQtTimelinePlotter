# EventTrackDrawingWidget.py
# Contains EventTrackDrawingWidget which draws several PhoEvent objects as rectangles or lines within a single track.

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget,QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize, pyqtSlot

from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidgetBase import TimelineTrackDrawingWidgetBase, ItemSelectionOptions
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_SelectionBase import TimelineTrackDrawingWidget_SelectionBase

from GUI.Model.Events.PhoDurationEvent_AnnotationComment import *
from GUI.UI.TextAnnotations.TextAnnotationDialog import *

from app.database.SqlAlchemyDatabase import create_TimestampedAnnotation, convert_TimestampedAnnotation, modify_TimestampedAnnotation, modify_TimestampedAnnotation_startDate, modify_TimestampedAnnotation_endDate

from GUI.Model.TrackType import TrackType, TrackConfigMixin, TrackConfigDataCacheMixin


"""
    This track draws a data file (.csv labjack file, for example) as a series of events along the timeline.
"""
class TimelineTrackDrawingWidget_DataFile(TrackConfigDataCacheMixin, TrackConfigMixin, TimelineTrackDrawingWidget_SelectionBase):
    # This defines a signal called 'hover_changed'/'selection_changed' that takes the trackID and the index of the child object that was hovered/selected
    default_shouldDismissSelectionUponMouseButtonRelease = True
    default_itemSelectionMode = ItemSelectionOptions.SingleSelection

    def __init__(self, trackConfig, totalStartTime, totalEndTime, database_connection, parent=None, wantsKeyboardEvents=False, wantsMouseEvents=True):
        self.trackConfig = trackConfig
        super(TimelineTrackDrawingWidget_DataFile, self).__init__(trackConfig.get_track_id(), totalStartTime, totalEndTime, [], database_connection=database_connection, parent=parent, wantsKeyboardEvents=wantsKeyboardEvents, wantsMouseEvents=wantsMouseEvents)
        # self.durationObjects = durationObjects
        self.instantaneousObjects = []
        # self.eventRect = np.repeat(QRect(0,0,0,0), len(durationObjects))
        self.instantaneousEventRect = np.repeat(QRect(0,0,0,0), len(self.instantaneousObjects))
        
        # Hovered Object
        self.hovered_object_index = None
        self.hovered_object = None
        self.hovered_object_rect = None
        self.hovered_duration_object_indicies = []

        # Selected Object
        self.selected_duration_object_indicies = []
        self.shouldDismissSelectionUponMouseButtonRelease = TimelineTrackDrawingWidget_DataFile.default_shouldDismissSelectionUponMouseButtonRelease
        self.itemSelectionMode = TimelineTrackDrawingWidget_DataFile.default_itemSelectionMode
        self.itemHoverMode = TimelineTrackDrawingWidget_SelectionBase.default_itemHoverMode

        self.setMouseTracking(True)

        self.trackConfig.cacheUpdated.connect(self.on_reloadModelFromConfigCache)
        self.reloadModelFromDatabase()
        

    # Override: TrackConfigDataCacheMixin
   # performReloadConfigCache(...): actually tells the config cache to update
    @pyqtSlot()
    def performReloadConfigCache(self):
        #TODO: figure out how to pass file path
        self.get_track_config().reload(self.database_connection.get_session(), self)
    
    
    ## Data Model Functions:
    # Updates the member variables from the database
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        # Load the latest behaviors and colors data from the database
        # tempAllAnnotationDataObjects = self.database_connection.load_annotation_events_from_database()
        # self.durationRecords = self.trackConfig.filter_records(self.database_connection.get_session())
        # Clear previous stuff before switching
        self.reset_on_reload()

        self.performReloadConfigCache()
        self.update()

    # on_reloadModelFromConfigCache(...): called when the config cache updates to reload the widget
    @pyqtSlot()
    def on_reloadModelFromConfigCache(self):
        # print("TimelineTrackDrawingWidget_DataFile.reloadModelFromConfigCache()")
        # TODO: close any open dialogs, etc, etc
        self.reset_on_reload()
        active_cache = self.trackConfig.get_cache()
        active_model_view_array = active_cache.get_model_view_array()
        self.durationRecords = []
        self.durationObjects = []

        for aContainerObj in active_model_view_array:
            self.durationRecords.append(aContainerObj.get_record())
            newAnnotationIndex = len(self.durationObjects)
            newAnnotationView = aContainerObj.get_view()
            newAnnotationView.setAccessibleName(str(newAnnotationIndex))
            self.durationObjects.append(newAnnotationView)

        self.update()
        

    # overrides
    def reset_hovered(self):
        super().reset_hovered()


    def reset_selected(self):
        super().reset_selected()


    def paintEvent( self, event ):
        qp = QtGui.QPainter()
        qp.begin( self )
        # TODO: minor speedup by re-using the array of QRect objects if the size doesn't change
        self.eventRect = np.repeat(QRect(0,0,0,0), len(self.durationObjects))
        self.instantaneousEventRect = np.repeat(QRect(0, 0, 0, 0), len(self.instantaneousObjects))

        ## TODO: Use viewport information to only draw the currently displayed rectangles instead of having to draw it all at once.
        drawRect = self.rect()

        # Draw the duration objects
        for (index, obj) in enumerate(self.durationObjects):
            self.eventRect[index] = obj.paint( qp, self.totalStartTime, self.totalEndTime, self.totalDuration, drawRect)
            
        # Draw the instantaneous event objects
        for (index, obj) in enumerate(self.instantaneousObjects):
            self.instantaneousEventRect[index] = obj.paint(qp, self.totalStartTime, self.totalEndTime, self.totalDuration, drawRect)

        qp.end()

    def set_active_filter(self, start_datetime, end_datetime):
        # Draw the duration objects
        for (index, obj) in enumerate(self.durationObjects):
            obj.is_deemphasized = not obj.overlaps_range(start_datetime, end_datetime)
        # Draw the instantaneous event objects
        for (index, obj) in enumerate(self.instantaneousObjects):
            obj.is_deemphasized = not obj.overlaps_range(start_datetime, end_datetime)
        self.update()


    def on_button_clicked(self, event):
        super().on_button_clicked(event)

    def on_button_released(self, event):
        super().on_button_released(event)
                
    def on_key_pressed(self, event):
        super().on_key_pressed(event)

    def on_key_released(self, event):
        super().on_key_released(event)

    def on_mouse_moved(self, event):
        super().on_mouse_moved(event)

