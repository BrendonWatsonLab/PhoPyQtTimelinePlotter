# EventTrackDrawingWidget.py
# Contains EventTrackDrawingWidget which draws several PhoEvent objects as rectangles or lines within a single track.

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget,QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QLinearGradient
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize, pyqtSlot

from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidgetBase import TimelineTrackDrawingWidgetBase, ItemSelectionOptions
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_EventsBase import TimelineTrackDrawingWidget_EventsBase

from GUI.UI.VideoEditDialog.VideoEditDialog import *
from GUI.Model.TrackType import TrackType, TrackConfigMixin


class TimelineTrackDrawingWidget_Videos(TrackConfigMixin, TimelineTrackDrawingWidget_EventsBase):
    # This defines a signal called 'hover_changed'/'selection_changed' that takes the trackID and the index of the child object that was hovered/selected
    default_shouldDismissSelectionUponMouseButtonRelease = False
    default_itemSelectionMode = ItemSelectionOptions.MultiSelection

    child_action_generate_thumbnails = pyqtSignal(int, object)


    def __init__(self, trackConfig, totalStartTime, totalEndTime, database_connection, parent=None, wantsKeyboardEvents=True, wantsMouseEvents=True):
        super(TimelineTrackDrawingWidget_Videos, self).__init__(trackConfig.get_track_id(), [], [], totalStartTime, totalEndTime, database_connection=database_connection, parent=parent, wantsKeyboardEvents=wantsKeyboardEvents, wantsMouseEvents=wantsMouseEvents)
        self.currNowPlayingVideoIndicies = []
        self.activeVideoEditDialog = None
        self.trackConfig = trackConfig
        self.child_action_generate_thumbnails.connect(self.parent().on_video_track_child_generate_thumbnails)

        self.trackConfig.cacheUpdated.connect(self.reloadModelFromConfigCache)


    ## Override:
    # attach_child_duration_object_signals(): called to attach the signals to the children duration objects
    def attach_child_duration_object_signals(self):
        super().attach_child_duration_object_signals()
        for aDurationObject in self.durationObjects:
            aDurationObject.on_generate_thumbnails.connect(self.on_child_action_generate_thumbnails)


    # Updates the member variables from the database
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        print("TimelineTrackDrawingWidget_Videos.reloadModelFromDatabase()")
        self.reset_on_reload()
        if self.parent is None:
            print("Invalid parent!")
            return
        else:
            pass
            # self.parent.


    @pyqtSlot()
    def reloadModelFromConfigCache(self):
        print("TimelineTrackDrawingWidget_Videos.reloadModelFromConfigCache()")
        self.reset_on_reload()
        active_cache = self.trackConfig.get_cache()
        active_model_view_array = active_cache.get_model_view_array()
        self.durationRecords = []
        self.durationObjects = []

        for aContainerObj in active_model_view_array:
            self.durationRecords.append(aContainerObj.get_record())
            newViewIndex = len(self.durationObjects)
            newView = aContainerObj.get_view()
            newView.setAccessibleName(str(newViewIndex))
            newView.on_create_marker_at_start.connect(self.on_create_playhead_selection)
            newView.on_create_marker_at_end.connect(self.on_create_playhead_selection)
            self.durationObjects.append(newView)

        # Attach the signals to the new durationObjects:
        self.attach_child_duration_object_signals()
        
        self.update()
        


    # Clears the "now playing" status from any videos in the track
    def clear_now_playing(self):
        for aPreviousPlayingVideoIndex in self.currNowPlayingVideoIndicies:
            self.durationObjects[aPreviousPlayingVideoIndex].set_is_playing(False)

    def set_now_playing(self, videoObjectIndex):
        if self.currNowPlayingVideoIndicies.__contains__(videoObjectIndex):
            # already playing, just return
            print("video with index {0} is already playing!".format(videoObjectIndex))
            return

        # Set other videos to not now_playing
        self.clear_now_playing()

        # Set new video to now_playing
        self.durationObjects[videoObjectIndex].set_is_playing(True)
        self.currNowPlayingVideoIndicies.append(videoObjectIndex)

        return


    def mouseDoubleClickEvent(self, event):
        print("TimelineTrackDrawingWidget_Videos.mouseDoubleClickEvent(): Mouse double clicked! ({0},{1})".format(event.x(), event.y()))

        newlySelectedObjectIndex = self.find_child_object(event.x(), event.y())

        if newlySelectedObjectIndex is not None:
            # Select the object
            didSelectionChange = self.select(newlySelectedObjectIndex)
            if (didSelectionChange):
                # Doesn't already contain the object
                self.durationObjects[newlySelectedObjectIndex].on_button_clicked(event)
                self.update()
                self.selection_changed.emit(self.trackID, newlySelectedObjectIndex)

            # Called once the selected partition object has been set the Partitioner should call "self.owning_parent_track.reloadModelFromDatabase()"
            self.on_video_modify_event()
        
        pass


    # Called by a specific child partition's menu to indicate that it should be edited in a new Partition Editor Dialog
    @pyqtSlot()    
    def on_video_modify_event(self):
        print("on_video_modify_event(...)")
        selectedVideoIndex = self.get_selected_event_index()
        selectedVideoObject = self.get_selected_duration_obj()
        
        if (selectedVideoObject):
            self.activeEditingVideoIndex = selectedVideoIndex
            self.activeVideoEditDialog = VideoEditDialog(self.database_connection, parent=self)
            self.activeVideoEditDialog.set_start_date(selectedVideoObject.startTime)
            self.activeVideoEditDialog.set_end_date(selectedVideoObject.endTime)
            # self.activeVideoEditDialog.set_type(selectedVideoObject.type_id)
            # self.activeVideoEditDialog.set_subtype(selectedVideoObject.subtype_id)
            self.activeVideoEditDialog.set_title(selectedVideoObject.name)
            self.activeVideoEditDialog.set_subtitle(str(selectedVideoObject.get_parent_url()))
            self.activeVideoEditDialog.set_body(str(selectedVideoObject.extended_data))
            print(selectedVideoObject.extended_data)
            
            sel_behavioral_box_id, sel_experiment_id, sel_cohort_id, sel_animal_id = selectedVideoObject.get_ids()
            self.activeVideoEditDialog.set_id_values(sel_behavioral_box_id, sel_experiment_id, sel_cohort_id, sel_animal_id)
            self.activeVideoEditDialog.set_is_original_video(selectedVideoObject.get_is_original_video())
            self.activeVideoEditDialog.on_commit.connect(self.try_update_video)
            self.activeVideoEditDialog.on_cancel.connect(self.video_dialog_canceled)
        else:
            print("Couldn't get active partition object to edit!!")
            self.activeEditingVideoIndex = None


    # Called when the partition edit dialog accept event is called.
    @pyqtSlot(datetime, datetime, int, int, int, int, bool)
    def try_update_video(self, start_date, end_date, behavioral_box_id, experiment_id, cohort_id, animal_id, is_original):
        # Tries to create a new comment
        print('try_update_video')
        # if (not (self.trackContextConfig.get_is_valid())):
        #     print('context is invalid! aborting try_update_video!')
        #     return
        
        if (not (self.activeEditingVideoIndex is None)):
            # Convert -1 values for type_id and subtype_id back into "None" objects. They had to be an Int to be passed through the pyQtSlot()
            # Note the values are record IDs (not indicies, so they're 1-indexed). This means that both -1 and 0 are invalid.
            if (behavioral_box_id < 1):
                behavioral_box_id = None
            if (experiment_id < 1):
                experiment_id = None
            if (cohort_id < 1):
                cohort_id = None
            if (animal_id < 1):
                animal_id = None
                
            self.update()
        else:
            print("Error: unsure what video to update!")
            return

    @pyqtSlot()
    def video_dialog_canceled(self):
        print('video_dialog_canceled')
        self.activeEditingVideoIndex = None


    @pyqtSlot(int, datetime)
    def on_create_playhead_selection(self, trackID, desired_datetime):
        print("TimelineTrackDrawingWidget_Videos.on_create_playhead_selection(trackID: {0}, desired_datetime: {1})".format(str(trackID), str(desired_datetime)))
        self.on_create_marker.emit(desired_datetime)
        # self.parent().on_create_playhead_selection(desired_datetime)


    @pyqtSlot(int)
    def on_child_action_generate_thumbnails(self, childIndex):
        print("TimelineTrackDrawingWidget_Videos.on_child_action_generate_thumbnails({0})".format(str(childIndex)))
        selected_obj = self.durationObjects[childIndex]
        if (selected_obj is None):
            print("ERROR: selected duration object is None! Can't perform action!")
            return
        else:
            # Call parent
            self.child_action_generate_thumbnails.emit(self.trackID, selected_obj)

        return