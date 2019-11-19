# EventTrackDrawingWidget.py
# Contains EventTrackDrawingWidget which draws several PhoEvent objects as rectangles or lines within a single track.

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QComboBox, QMenu
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize, pyqtSlot

from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidgetBase import TimelineTrackDrawingWidgetBase, ItemSelectionOptions

## IMPORT:
# from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_SelectionBase import TimelineTrackDrawingWidget_SelectionBase

#  "A Base with selections"
#  
class TimelineTrackDrawingWidget_SelectionBase(TimelineTrackDrawingWidgetBase):
    default_shouldDismissSelectionUponMouseButtonRelease = False
    default_itemSelectionMode = ItemSelectionOptions.SingleSelection

    def __init__(self, trackID, totalStartTime, totalEndTime, durationObjects, database_connection, parent=None, wantsKeyboardEvents=True, wantsMouseEvents=True):
        super(TimelineTrackDrawingWidget_SelectionBase, self).__init__(trackID, totalStartTime, totalEndTime, database_connection=database_connection, parent=parent, wantsKeyboardEvents=wantsKeyboardEvents, wantsMouseEvents=wantsMouseEvents)
        self.reloadModelFromDatabase()
        self.durationObjects = durationObjects
        self.eventRect = np.repeat(QRect(0,0,0,0), len(durationObjects))

        # Hovered Object
        self.hovered_object_index = None
        self.hovered_object = None
        self.hovered_object_rect = None
        # Selected Object
        self.selected_duration_object_indicies = []
        self.shouldDismissSelectionUponMouseButtonRelease = TimelineTrackDrawingWidget_SelectionBase.default_shouldDismissSelectionUponMouseButtonRelease
        self.itemSelectionMode = TimelineTrackDrawingWidget_SelectionBase.default_itemSelectionMode

    
    # Returns the currently selected partition index or None if none are selected
    def get_selected_event_index(self):
        if (len(self.selected_duration_object_indicies) > 0):
            # Deselect previously selected item
            prevSelectedItemIndex = self.selected_duration_object_indicies[0]
            if (not (prevSelectedItemIndex is None)):
                return prevSelectedItemIndex
            else:
                return None
        else:
            return None

    # Returns the currently selected partition object or None if none are selected
    def get_selected_duration_obj(self):
        prevSelectedItemIndex = self.get_selected_event_index()
        if (not (prevSelectedItemIndex is None)):
            prevSelectedDurationObj = self.durationObjects[prevSelectedItemIndex]
            if (prevSelectedDurationObj):
                return prevSelectedDurationObj
            else:
                return None
        else:
            return None
    

    # Returns the index of the child object that the (x, y) point falls within, or None if it doesn't fall within an event.
    def find_child_object(self, event_x, event_y):
        clicked_object_index = None
        for (index, aRect) in enumerate(self.eventRect):
            if aRect.contains(event_x, event_y):
                clicked_object_index = index
                break
        return clicked_object_index

    def deselect_all(self):
        # print("deselect_all()")
        while (len(self.selected_duration_object_indicies) > 0):
            prevSelectedItemIndex = self.selected_duration_object_indicies[0]
            self.selected_duration_object_indicies.remove(prevSelectedItemIndex)
            self.durationObjects[prevSelectedItemIndex].set_state_deselected()

    def select(self, new_selection_index):
            # Select the object
            if (self.selected_duration_object_indicies.__contains__(new_selection_index)):
                # Already contains the object.
                return False
            else:
                # If in single selection mode, be sure to deselect any previous selections before selecting a new one.
                if (self.itemSelectionMode is ItemSelectionOptions.SingleSelection):
                    self.deselect_all()
                # Doesn't already contain the object
                self.selected_duration_object_indicies.append(new_selection_index)
                self.durationObjects[new_selection_index].set_state_selected()
                return True

    def deselect(self, selection_index):
            # Select the object
            if (self.selected_duration_object_indicies.__contains__(selection_index)):
                # Already contains the object.
                self.selected_duration_object_indicies.remove(selection_index)
                self.durationObjects[selection_index].set_state_deselected()
                return True
            else:
                return False



    def on_button_clicked(self, event):
        newlySelectedObjectIndex = self.find_child_object(event.x(), event.y())

        if newlySelectedObjectIndex is None:
            self.deselect_all()
            self.selected_duration_object_indicies = [] # Empty all the objects
            self.selection_changed.emit(self.trackID, -1)
        else:
            # Select the object
            didSelectionChange = self.select(newlySelectedObjectIndex)
            if (not didSelectionChange):
                # Already contains the object.
                return
            else:
                # Doesn't already contain the object
                self.durationObjects[newlySelectedObjectIndex].on_button_clicked(event)
                self.update()
                self.selection_changed.emit(self.trackID, newlySelectedObjectIndex)

    def on_button_released(self, event):
        # Check if we want to dismiss the selection when the mouse button is released (requiring the user to hold down the button to see the results)
        needs_update = False                    
        newlySelectedObjectIndex = self.find_child_object(event.x(), event.y())

        if newlySelectedObjectIndex is None:
            if self.shouldDismissSelectionUponMouseButtonRelease:
                self.deselect_all()
                self.selection_changed.emit(self.trackID, -1) # Deselect
            # No Durations to create
            return
        else:
            cut_partition_index = newlySelectedObjectIndex
            if self.shouldDismissSelectionUponMouseButtonRelease:
                didSelectionChange = self.deselect(newlySelectedObjectIndex)
                if (not didSelectionChange):
                    # Already contains the object.
                    return
                else:
                    # Doesn't already contain the object
                    self.durationObjects[newlySelectedObjectIndex].on_button_released(event)
                    self.selection_changed.emit(self.trackID, newlySelectedObjectIndex) #TODO: do we need to do this?
                    needs_update = True
            
        if needs_update:
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
            self.hovered_object = self.durationObjects[self.hovered_object_index]
            self.hovered_object_rect = self.eventRect[self.hovered_object_index]
            text = "event: {0}\nstart_time: {1}\nend_time: {2}\nduration: {3}".format(self.hovered_object.name, self.hovered_object.startTime, self.hovered_object.endTime, self.hovered_object.computeDuration())
            QToolTip.showText(event.globalPos(), text, self, self.hovered_object_rect)
            self.hover_changed.emit(self.trackID, self.hovered_object_index)

