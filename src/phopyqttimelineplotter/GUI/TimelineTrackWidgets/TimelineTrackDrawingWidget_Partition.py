# EventTrackDrawingWidget.py
# Contains EventTrackDrawingWidget which draws several PhoEvent objects as rectangles or lines within a single track.

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QComboBox, QMenu
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize, pyqtSlot

from phopyqttimelineplotter.GUI.Model.Partitions import *
from phopyqttimelineplotter.GUI.TimelineTrackWidgets.TimelineTrackDrawingWidgetBase import *

from phopyqttimelineplotter.GUI.UI.PartitionEditDialog.PartitionEditDialog import *
from phopyqttimelineplotter.GUI.Model.TrackType import TrackType, TrackConfigMixin, TrackConfigDataCacheMixin

from phopyqttimelineplotter.GUI.UI.DialogComponents.AbstractDialogMixins import DialogObjectIdentifier


## TODO:
"""
TODO: Add "undo" functionality to creating cuts. Can use the "cutObjects" to find the last created cut, find the partition created at that timestamp, grab its endTime and then delete it, and then set the endTime of the partition just before it.

"""

# Each track has a (Context, Subcontext) pair that define what types of CategoricalDurationLabels it creates
# TODO: the track context config should affect what type/subtype options are loaded into the partition edit dialog.
class TrackContextConfig(QObject):
    def __init__(self, contextName, subcontextIndex=0, parent=None):
        super().__init__(parent=parent)
        self.is_valid = False
        self.contextName = contextName
        self.subcontextIndex = subcontextIndex
        self.context = None
        self.subcontext = None

    def get_context(self):
        return self.context

    def get_subcontext(self):
        return self.subcontext

    def get_context_name(self):
        return self.contextName

    def get_subcontext_index(self):
        return self.subcontextIndex

    def get_is_valid(self):
        return self.is_valid

    # update_on_load(...): called from owner's reloadModelFromDatabase(...) with the valid context and subcontext objects
    def update_on_load(self, contextObj, subcontextObj):
        self.context = contextObj
        self.subcontext = subcontextObj
        self.is_valid = ((self.context is not None) and (self.subcontext is not None))

    def __str__(self):
        # return 'TrackFilterBase: behavioral_box_ids: {0}, experiment_ids: {1}, cohort_ids: {2}, animal_ids: {3}'.format(self.behavioral_box_ids, self.experiment_ids, self.cohort_ids, self.animal_ids)
        return '({0})'.format(self.get_context_name())



# Consts of N "Cuts" that separate a block into N+1 "Partitions"
#  
class TimelineTrackDrawingWidget_Partition(TrackConfigDataCacheMixin, TrackConfigMixin, TimelineTrackDrawingWidgetBase):
    default_shouldDismissSelectionUponMouseButtonRelease = False
    default_itemSelectionMode = ItemSelectionOptions.SingleSelection

    def __init__(self, trackConfig, totalStartTime, totalEndTime, database_connection, trackContextConfig, parent=None, wantsKeyboardEvents=True, wantsMouseEvents=True):
        super(TimelineTrackDrawingWidget_Partition, self).__init__(trackConfig.get_track_id(), totalStartTime, totalEndTime, database_connection=database_connection, parent=parent, wantsKeyboardEvents=wantsKeyboardEvents, wantsMouseEvents=wantsMouseEvents)
        
        self.trackContextConfig = trackContextConfig
        
        self.trackConfig = trackConfig
        self.trackConfig.cacheUpdated.connect(self.reloadModelFromConfigCache)

        self.durationRecords = []
        self.durationObjects = []

        self.partitionManager = None
        # self.partitionManager is initialized in self.reloadModelFromDatabase() if it's None
        self.reloadModelFromDatabase()

        self.reinitialize_from_partition_manager()
        ## TODO: can reconstruct partitions from cutObjects, but can't recover the specific partition's info.
        self.cutObjects = []
        self.instantaneousEventRect = np.repeat(QRect(0,0,0,0), len(self.cutObjects))
        # Hovered Object
        self.hovered_object_index = None
        self.hovered_object = None
        self.hovered_object_rect = None
        # Selected Object
        self.selected_partition_object_indicies = []
        self.shouldDismissSelectionUponMouseButtonRelease = TimelineTrackDrawingWidget_Partition.default_shouldDismissSelectionUponMouseButtonRelease
        self.itemSelectionMode = TimelineTrackDrawingWidget_Partition.default_itemSelectionMode

        self.activePartitionEditDialog = None
        self.update()


    ## Data Model Functions:
    # Updates the member variables from the database
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        # self.reset_on_reload()

        # Load the latest behaviors and colors data from the database
        self.behaviorGroups = self.database_connection.load_behavior_groups_from_database()
        self.behaviors = self.database_connection.load_behaviors_from_database()
        self.contextsDict = self.database_connection.load_contexts_from_database()
        self.subcontexts = self.database_connection.load_subcontexts_from_database()

        # The partition manager is created/updated in the self.reloadModelFromConfigCache(...) function
        self.performReloadConfigCache()
        self.update()

    @pyqtSlot()
    def reloadModelFromConfigCache(self):
        # print("TimelineTrackDrawingWidget_Partition.reloadModelFromConfigCache()")
        active_cache = self.trackConfig.get_cache()
        active_model_view_array = active_cache.get_model_view_array()
        self.durationRecords = []
        self.durationObjects = []

        # For the partition track, just add the records, not the views. In fact, the config cache doesn't generate any views for partition tracks because we generate them in the partition manager
        for aContainerObj in active_model_view_array:
            self.durationRecords.append(aContainerObj.get_record())

        # Update partitionManager:
        if self.partitionManager is None:
            self.partitionManager = Partitioner(self.totalStartTime, self.totalEndTime, self, self.database_connection, name="name", partitionViews=None, partitionDataObjects=self.durationRecords)
        else:
            # Builds the partition objects, meaning both the record and view components
            self.partitionManager.on_reload_partition_records(self.durationRecords)


        self.reinitialize_from_partition_manager()
        self.update()


    def reinitialize_from_partition_manager(self):
        self.partitions = self.partitionManager.get_partitions()
        self.eventRect = np.repeat(QRect(0,0,0,0), len(self.partitions))


    # Find the next event
    def find_next_event(self, following_datetime):
        for (index, obj) in enumerate(self.partitions):
            if (obj.get_view().startTime > following_datetime):
                return (index, obj.get_view())
        return None # If there is no next event, return None


    # Find the previous event
    def find_previous_event(self, preceeding_datetime):

        best_found_candidate_index = None
        best_found_candidate_object = None

        for (index, obj) in enumerate(self.partitions):
            if (obj.get_view().endTime < preceeding_datetime):
                best_found_candidate_index = index
                best_found_candidate_object = obj.get_view()
            else:
                # otherwise if the object's endTime is later than our desired preceeding_datetime, we have our candidate to return
                break
            
        if ((best_found_candidate_index is None) and (best_found_candidate_object is None)):
            return None
        else:
            return (best_found_candidate_index, best_found_candidate_object)



    # Called by a specific child partition's (double click or menu option) to indicate that it should be edited in a new Partition Editor Dialog
    @pyqtSlot(int)    
    def on_partition_modify_event(self, childIndex):
        # print("on_partition_modify_event(...)")

        selectedPartitionIndex = childIndex
        selectedPartitionObj = self.partitions[childIndex]
        selectedPartitionViewObject = selectedPartitionObj.get_view()

        if ((not (selectedPartitionViewObject is None))):
            self.activePartitionEditDialog = PartitionEditDialog(self.database_connection, parent=self)
            self.activePartitionEditDialog.set_referred_object_identifiers(self.get_trackID(), selectedPartitionIndex)
            self.activePartitionEditDialog.set_start_date(selectedPartitionViewObject.startTime)
            self.activePartitionEditDialog.set_end_date(selectedPartitionViewObject.endTime)
            self.activePartitionEditDialog.set_type(selectedPartitionViewObject.type_id)
            self.activePartitionEditDialog.set_subtype(selectedPartitionViewObject.subtype_id)
            self.activePartitionEditDialog.set_title(selectedPartitionViewObject.name)
            self.activePartitionEditDialog.set_subtitle(selectedPartitionViewObject.subtitle)
            self.activePartitionEditDialog.set_body(selectedPartitionViewObject.body)

             ## SHOULD BE SET TO TRACK's global values for these variables.
            ## TODO: the track can have multiple values
            sel_behavioral_box_id, sel_experiment_id, sel_cohort_id, sel_animal_id = None, None, None, None
            sel_behavioral_box_ids, sel_experiment_ids, sel_cohort_ids, sel_animal_ids = self.trackConfig.get_filter().get_ids()
            if sel_behavioral_box_ids is not None:
                sel_behavioral_box_id = sel_behavioral_box_ids[0]
            if sel_experiment_ids is not None:
                sel_experiment_id = sel_experiment_ids[0]   
            if sel_cohort_ids is not None:
                sel_cohort_id = sel_cohort_ids[0]
            if sel_animal_ids is not None:
                sel_animal_id = sel_animal_ids[0]

            self.activePartitionEditDialog.set_id_values(sel_behavioral_box_id, sel_experiment_id, sel_cohort_id, sel_animal_id)
            self.activePartitionEditDialog.set_id_frame_editability(False) # Ensure the id options aren't editable. For partitions they're determined entirely by the track's config.

            self.activePartitionEditDialog.on_commit.connect(self.try_update_partition)
            self.activePartitionEditDialog.on_cancel.connect(self.partition_dialog_canceled)
        else:
            print("Couldn't get active partition object to edit!!")

    # Returns the currently selected partition index or None if none are selected
    def get_selected_partition_index(self):
        if (len(self.selected_partition_object_indicies) > 0):
            # Deselect previously selected item
            prevSelectedItemIndex = self.selected_partition_object_indicies[0]
            if (not (prevSelectedItemIndex is None)):
                return prevSelectedItemIndex
            else:
                return None
        else:
            return None

    # Returns the currently selected partition object or None if none are selected
    ## TODO: see where this is used, and return a view if that's what it's expecting
    def get_selected_partition(self):
        prevSelectedItemIndex = self.get_selected_partition_index()
        if (not (prevSelectedItemIndex is None)):
            prevSelectedPartitionObj = self.partitions[prevSelectedItemIndex]
            if (prevSelectedPartitionObj):
                return prevSelectedPartitionObj
            else:
                return None
        else:
            return None
    
    # Ohhh, paint event is only passing the displayed rectangle in the event, so when it's in a scroll view, only the part that's on the screen is being drawn.
    # But if that's true, why isn't it appearing unchanged when we scroll?
    def paintEvent( self, event ):
        qp = QtGui.QPainter()
        qp.begin( self )
        # TODO: minor speedup by re-using the array of QRect objects if the size doesn't change
        self.eventRect = np.repeat(QRect(0,0,0,0), len(self.partitions))
        self.instantaneousEventRect = np.repeat(QRect(0, 0, 0, 0), len(self.cutObjects))

        # Draw the trace cursor
        # qp.setPen(QtGui.QPen(EventsDrawingWindow.TraceCursorColor, 20.0, join=Qt.MiterJoin))
        # qp.drawRect(event.rect().x(), event.rect().y(), EventsDrawingWindow.TraceCursorWidth, self.height())

        ## TODO: Use viewport information to only draw the currently displayed rectangles instead of having to draw it all at once.
        # print('eventRect:', event.rect())
        # print('selftRect:', self.rect())
        # print('')

        # drawRect = event.rect()
        drawRect = self.rect()

        # Draw the duration objects
        for (index, obj) in enumerate(self.partitions):
            obj.get_view().update()
            self.eventRect[index] = obj.get_view().paint(qp, self.totalStartTime, self.totalEndTime, self.totalDuration, drawRect)
        # Draw the instantaneous event objects
        for (index, obj) in enumerate(self.cutObjects):
            self.instantaneousEventRect[index] = obj.paint(qp, self.totalStartTime, self.totalEndTime, self.totalDuration, drawRect)

        qp.end()

    def mouseDoubleClickEvent(self, event):
        print("Mouse double clicked! ({0},{1})".format(event.x(), event.y()))

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
            self.on_partition_modify_event(newlySelectedObjectIndex)
        
        pass


    # Returns the index of the child object that the (x, y) point falls within, or None if it doesn't fall within an event.
    def find_child_object(self, event_x, event_y):
        clicked_object_index = None
        for (index, aRect) in enumerate(self.eventRect):
            if aRect.contains(event_x, event_y):
                clicked_object_index = index
                break
        return clicked_object_index

    def cut_partition(self, partition_index, cut_x):
        # Creates a new cut at the specified position.
        cut_duration_offset = self.offset_to_duration(cut_x)
        cut_datetime = self.offset_to_datetime(cut_x)

        if self.partitionManager.cut_partition(partition_index, cut_datetime):
                # Cut successful!
                print("Cut successful! Cut at ", partition_index)
                # self.cutObjects.append(PhoDurationEvent(cut_datetime))
                # Update partitions:
                self.reinitialize_from_partition_manager()
                ## TODO: This may not be needed, as if a cut was made partition manager should call self.reloadModelFromDatabase()... but this doesn't reinitialize
                self.update()
                return True
        else:
            return False
        
    def set_active_filter(self, start_datetime, end_datetime):
        # Draw the duration objects
        for (index, obj) in enumerate(self.partitions):
            obj.get_view().is_deemphasized = not obj.overlaps_range(start_datetime, end_datetime)
        # Draw the instantaneous event objects
        for (index, obj) in enumerate(self.cutObjects):
            obj.is_deemphasized = not obj.overlaps_range(start_datetime, end_datetime)
        self.update()

    def on_button_clicked(self, event):
        newlySelectedObjectIndex = self.find_child_object(event.x(), event.y())

        if newlySelectedObjectIndex is None:
            self.selected_partition_object_indicies = [] # Empty all the objects
            self.selection_changed.emit(self.trackID, -1)
        else:
            # Select the object
            if (self.selected_partition_object_indicies.__contains__(newlySelectedObjectIndex)):
                # Already contains the object.
                return
            else:
                # If in single selection mode, be sure to deselect any previous selections before selecting a new one.
                if (self.itemSelectionMode is ItemSelectionOptions.SingleSelection):
                    if (len(self.selected_partition_object_indicies) > 0):
                        # Deselect previously selected item
                        prevSelectedItemIndex = self.selected_partition_object_indicies[0]
                        self.selected_partition_object_indicies.remove(prevSelectedItemIndex)
                        self.partitions[prevSelectedItemIndex].get_view().on_button_released(event)
                        # self.selection_changed.emit(self.trackID, newlySelectedObjectIndex) # TODO: need to update the selection to deselect the old event?
                        

                # Doesn't already contain the object
                self.selected_partition_object_indicies.append(newlySelectedObjectIndex)
                self.partitions[newlySelectedObjectIndex].get_view().on_button_clicked(event)
                self.update()
                self.selection_changed.emit(self.trackID, newlySelectedObjectIndex)

    def on_button_released(self, event):
        # Check if we want to dismiss the selection when the mouse button is released (requiring the user to hold down the button to see the results)
        needs_update = False                    
        newlySelectedObjectIndex = self.find_child_object(event.x(), event.y())

        if newlySelectedObjectIndex is None:
            if self.shouldDismissSelectionUponMouseButtonRelease:
                self.selection_changed.emit(self.trackID, -1) # Deselect
            # No partitions to create
            return
        else:
            cut_partition_index = newlySelectedObjectIndex
            if self.shouldDismissSelectionUponMouseButtonRelease:
                if (self.selected_partition_object_indicies.__contains__(newlySelectedObjectIndex)):
                    # Already contains the object.
                    self.selected_partition_object_indicies.remove(newlySelectedObjectIndex)
                    self.partitions[newlySelectedObjectIndex].get_view().on_button_released(event)
                    self.selection_changed.emit(self.trackID, newlySelectedObjectIndex)
                    needs_update = True
                else:
                    # Doesn't already contain the object
                    return
            
            if event.button() == Qt.LeftButton:
                print("partitionTrack: Left click")
            elif event.button() == Qt.RightButton:
                print("partitionTrack: Right click")
                prevHoveredObj = self.hovered_object
                if prevHoveredObj:
                    prevHoveredObj.on_button_released(event)
                else:
                    print('partitionTrack: No valid hoverred object')

                prevSelectedPartitionViewObj = self.get_selected_partition().get_view()
                if (prevSelectedPartitionViewObj):
                    prevSelectedPartitionViewObj.on_button_released(event)
                else:
                    print('partitionTrack: No valid selection object')


            elif event.button() == Qt.MiddleButton:
                print("partitionTrack: Middle click")
                # Create the partition cut:
                was_cut_made = self.cut_partition(cut_partition_index, event.x())
                if(was_cut_made):
                    needs_update = True
            else:
                print("partitionTrack: Unknown click event!")
            
        if needs_update:
            self.update()
            
    def on_key_pressed(self, event):
        gey = event.key()
        self.func = (None, None)
        print("partitionTrack: on_key_pressed(...)")
        if gey == Qt.Key_M:
            print("partitionTrack: Key 'm' pressed!")
            prevHoveredObj = self.hovered_object
            if prevHoveredObj:
                prevHoveredObj.on_key_pressed(event)
            else:
                print('partitionTrack: No valid hoverred object')

            prevSelectedPartitionObj = self.get_selected_partition().get_view()
            if (prevSelectedPartitionObj):
                prevSelectedPartitionObj.on_key_pressed(event)
            else:
                print('partitionTrack: No valid selection object')

        elif gey == Qt.Key_Right:
            print("partitionTrack: Right key pressed!, call drawFundBlock()")
            self.func = (self.drawFundBlock, {})
            self.mModified = True
            self.update()
            self.nextRegion()
        elif gey == Qt.Key_5:
            print("partitionTrack: #5 pressed, call drawNumber()")
            self.func = (self.drawNumber, {"notePoint": QPoint(100, 100)})
            self.mModified = True
            self.update()

    def on_mouse_moved(self, event):
        self.hovered_object_index = self.find_child_object(event.x(), event.y())
        if self.hovered_object_index is None:
            # No object hovered
            QToolTip.hideText()
            self.hovered_object = None
            self.hovered_object_rect = None
            self.hover_changed.emit(self.trackID, -1)
        else:
            self.hovered_object = self.partitions[self.hovered_object_index].get_view()
            self.hovered_object_rect = self.eventRect[self.hovered_object_index]
            text = "event: {0}\nstart_time: {1}\nend_time: {2}\nduration: {3}".format(self.hovered_object.name, self.get_full_date_time_string(self.hovered_object.startTime), self.get_full_date_time_string(self.hovered_object.endTime), self.hovered_object.computeDuration())
            QToolTip.showText(event.globalPos(), text, self, self.hovered_object_rect)
            self.hover_changed.emit(self.trackID, self.hovered_object_index)

        super().on_mouse_moved(event)

    # Called when the partition edit dialog accept event is called.
    @pyqtSlot(DialogObjectIdentifier, datetime, datetime, str, str, str, int, int)
    def try_update_partition(self, partition_identifier, start_date, end_date, title, subtitle, body, type_id, subtype_id):
        # Tries to create a new comment
        print('try_update_partition')
        if (not (self.trackContextConfig.get_is_valid())):
            print('context is invalid! aborting try_update_partition!')
            return

        dialog_child_partition_index = partition_identifier.childID

        # if the referred to child index exists, and is valid within the current array, continue
        if ((dialog_child_partition_index is not None) and (0 <= dialog_child_partition_index <= (len(self.partitions)-1))):        
            # Convert -1 values for type_id and subtype_id back into "None" objects. They had to be an Int to be passed through the pyQtSlot()
            # Note the values are record IDs (not indicies, so they're 1-indexed). This means that both -1 and 0 are invalid.
            if (type_id < 1):
                type_id = None
            
            if (subtype_id < 1):
                subtype_id = None
                
            print('Modifying partition[{0}]: (type_id: {1}, subtype_id: {2})'.format(dialog_child_partition_index, type_id, subtype_id))
            
            # Get new color associated with the modified subtype_id
            if ((type_id is None) or (subtype_id is None)):
                newColor = PhoDurationEvent_Partition.ColorBase
            else:
                newColor = self.behaviors[subtype_id-1].primaryColor.get_QColor()
            
            self.partitionManager.modify_partition(dialog_child_partition_index, start_date, end_date, title, subtitle, body, type_id, subtype_id, newColor)
            print('Modified partition[{0}]: (type_id: {1}, subtype_id: {2})'.format(dialog_child_partition_index, type_id, subtype_id))
            self.reinitialize_from_partition_manager()
            self.update()
            # Save to database
            # TODO: currently all saved partitions must be of the same context and subcontext.
            self.partitionManager.save_partitions_to_database()
        else:
            print("Error: try_update_partition(...): dialog_child_partition_index {0} is not valid".format(str(dialog_child_partition_index)))
            # print("Error: unsure what partition to update!")
            return

    @pyqtSlot(DialogObjectIdentifier)
    def partition_dialog_canceled(self, partition_identifier):
        print('comment_Dialog_canceled')


    # try_cut_partition(...): tries to cut the partition programmatically at the specified datetime
    def try_cut_partition(self, cut_datetime):
        needs_update = False
        cut_offset_x = self.datetime_to_offset(cut_datetime)
        newlySelectedObjectIndex = self.find_child_object(cut_offset_x, 0)
        if (newlySelectedObjectIndex is None):
            print("couldn't cut partition!")
            return
        
        # Create the partition cut:
        was_cut_made = self.cut_partition(newlySelectedObjectIndex, cut_offset_x)
        if(was_cut_made):
            needs_update = True
        
        if needs_update:
            self.update()



        

