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

class TimelineTrackDrawingWidget_Videos(TimelineTrackDrawingWidget_EventsBase):
    # This defines a signal called 'hover_changed'/'selection_changed' that takes the trackID and the index of the child object that was hovered/selected
    default_shouldDismissSelectionUponMouseButtonRelease = True
    default_itemSelectionMode = ItemSelectionOptions.MultiSelection

    def __init__(self, trackID, durationObjects, instantaneousObjects, totalStartTime, totalEndTime, database_connection, parent=None, wantsKeyboardEvents=True, wantsMouseEvents=True):
        super(TimelineTrackDrawingWidget_Videos, self).__init__(trackID, durationObjects, instantaneousObjects, totalStartTime, totalEndTime, database_connection=database_connection, parent=parent, wantsKeyboardEvents=wantsKeyboardEvents, wantsMouseEvents=wantsMouseEvents)
        self.currNowPlayingVideoIndicies = []
        self.activeVideoEditDialog = None

    def set_now_playing(self, videoObjectIndex):
        if self.currNowPlayingVideoIndicies.__contains__(videoObjectIndex):
            # already playing, just return
            print("video with index {0} is already playing!".format(videoObjectIndex))
            return

        # Set other videos to not now_playing
        for aPreviousPlayingVideoIndex in self.currNowPlayingVideoIndicies:
            self.durationObjects[aPreviousPlayingVideoIndex].set_is_playing(False)

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
            self.activeVideoEditDialog.set_subtitle(str(selectedVideoObject.get_video_url()))
            self.activeVideoEditDialog.set_body(str(selectedVideoObject.extended_data))
            self.activeVideoEditDialog.on_commit.connect(self.try_update_video)
            self.activeVideoEditDialog.on_cancel.connect(self.video_dialog_canceled)
        else:
            print("Couldn't get active partition object to edit!!")
            self.activeEditingVideoIndex = None


    # Called when the partition edit dialog accept event is called.
    def try_update_video(self, start_date, end_date, title, subtitle, body, type_id, subtype_id):
        # Tries to create a new comment
        print('try_update_video')
        # if (not (self.trackContextConfig.get_is_valid())):
        #     print('context is invalid! aborting try_update_video!')
        #     return
        
        # if (not (self.activeEditingVideoIndex is None)):
        #     # Convert -1 values for type_id and subtype_id back into "None" objects. They had to be an Int to be passed through the pyQtSlot()
        #     # Note the values are record IDs (not indicies, so they're 1-indexed). This means that both -1 and 0 are invalid.
        #     if (type_id < 1):
        #         type_id = None
            
        #     if (subtype_id < 1):
        #         subtype_id = None
                
        #     print('Modifying partition[{0}]: (type_id: {1}, subtype_id: {2})'.format(self.activeEditingVideoIndex, type_id, subtype_id))
            
        #     # Get new color associated with the modified subtype_id
        #     if ((type_id is None) or (subtype_id is None)):
        #         newColor = PhoDurationEvent_Partition.ColorBase
        #     else:
        #         newColor = self.behaviors[subtype_id-1].primaryColor.get_QColor()
            
        #     self.partitionManager.modify_partition(self.activeEditingVideoIndex, start_date, end_date, title, subtitle, body, type_id, subtype_id, newColor)
        #     print('Modified partition[{0}]: (type_id: {1}, subtype_id: {2})'.format(self.activeEditingVideoIndex, type_id, subtype_id))
        #     self.reinitialize_from_partition_manager()
        #     self.update()
        #     # Save to database
        #     # TODO: currently all saved partitions must be of the same context and subcontext.
        #     self.partitionManager.save_partitions_to_database()
        # else:
        #     print("Error: unsure what partition to update!")
        #     return

    def video_dialog_canceled(self):
        print('video_dialog_canceled')
        self.activeEditingVideoIndex = None
