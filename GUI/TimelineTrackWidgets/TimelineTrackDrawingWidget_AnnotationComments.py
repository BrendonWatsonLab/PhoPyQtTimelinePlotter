# EventTrackDrawingWidget.py
# Contains EventTrackDrawingWidget which draws several PhoEvent objects as rectangles or lines within a single track.

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget,QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidgetBase import *
from GUI.Model.PhoDurationEvent_AnnotationComment import *
from GUI.UI.TextAnnotations.TextAnnotationDialog import *

from app.database.SqlAlchemyDatabase import load_annotation_events_from_database, save_annotation_events_to_database, create_TimestampedAnnotation, convert_TimestampedAnnotation

class TimelineTrackDrawingWidget_AnnotationComments(TimelineTrackDrawingWidgetBase):
    # This defines a signal called 'hover_changed'/'selection_changed' that takes the trackID and the index of the child object that was hovered/selected
    default_shouldDismissSelectionUponMouseButtonRelease = True
    default_itemSelectionMode = ItemSelectionOptions.MultiSelection

    def __init__(self, trackID, durationObjects, instantaneousObjects, totalStartTime, totalEndTime):
        super(TimelineTrackDrawingWidget_AnnotationComments, self).__init__(trackID, totalStartTime, totalEndTime)
        self.durationObjects = durationObjects
        self.instantaneousObjects = instantaneousObjects
        self.eventRect = np.repeat(QRect(0,0,0,0), len(durationObjects))
        self.instantaneousEventRect = np.repeat(QRect(0,0,0,0), len(instantaneousObjects))
        # Hovered Object
        self.hovered_object_index = None
        self.hovered_object = None
        self.hovered_object_rect = None
        # Selected Object
        # self.selected_object_index = None
        self.selected_duration_object_indicies = []
        self.shouldDismissSelectionUponMouseButtonRelease = TimelineTrackDrawingWidget_AnnotationComments.default_shouldDismissSelectionUponMouseButtonRelease
        self.itemSelectionMode = TimelineTrackDrawingWidget_AnnotationComments.default_itemSelectionMode

        self.annotationEditingDialog = None
        self.annotationDataObjects = []
        self.annotationDataObjects = load_annotation_events_from_database('/Users/pho/repo/PhoPyQtTimelinePlotter/BehavioralBoxDatabase.db')
        self.rebuildDrawnObjects()

    # Rebuilds the GUI event objects from the self.annotationDataObjects
    def rebuildDrawnObjects(self):
        self.durationObjects = []
        for aDataObj in self.annotationDataObjects:
            # Create the graphical annotation object
            newAnnotation = convert_TimestampedAnnotation(aDataObj)
            # newAnnotation = PhoDurationEvent_AnnotationComment(start_date, end_date, body, title, subtitle)
            self.durationObjects.append(newAnnotation)

    
    def paintEvent( self, event ):
        qp = QtGui.QPainter()
        qp.begin( self )
        # TODO: minor speedup by re-using the array of QRect objects if the size doesn't change
        self.eventRect = np.repeat(QRect(0,0,0,0), len(self.durationObjects))
        self.instantaneousEventRect = np.repeat(QRect(0, 0, 0, 0), len(self.instantaneousObjects))

        # Draw the trace cursor
        # qp.setPen(QtGui.QPen(EventsDrawingWindow.TraceCursorColor, 20.0, join=Qt.MiterJoin))
        # qp.drawRect(event.rect().x(), event.rect().y(), EventsDrawingWindow.TraceCursorWidth, self.height())

        ## TODO: Use viewport information to only draw the currently displayed rectangles instead of having to draw it all at once.
        # drawRect = event.rect()
        drawRect = self.rect()

        # Draw the duration objects
        for (index, obj) in enumerate(self.durationObjects):
            self.eventRect[index] = obj.paint( qp, self.totalStartTime, self.totalEndTime, self.totalDuration, drawRect)
            
        # Draw the instantaneous event objects
        for (index, obj) in enumerate(self.instantaneousObjects):
            self.instantaneousEventRect[index] = obj.paint(qp, self.totalStartTime, self.totalEndTime, self.totalDuration, drawRect)

        qp.end()

    # Returns the index of the child object that the (x, y) point falls within, or None if it doesn't fall within an event.
    def find_child_object(self, event_x, event_y):
        clicked_object_index = None
        for (index, aRect) in enumerate(self.eventRect):
            if aRect.contains(event_x, event_y):
                clicked_object_index = index
                break
        return clicked_object_index

    def set_active_filter(self, start_datetime, end_datetime):
        # Draw the duration objects
        for (index, obj) in enumerate(self.durationObjects):
            obj.is_deemphasized = not obj.overlaps_range(start_datetime, end_datetime)
        # Draw the instantaneous event objects
        for (index, obj) in enumerate(self.instantaneousObjects):
            obj.is_deemphasized = not obj.overlaps_range(start_datetime, end_datetime)
        self.update()

    def on_button_clicked(self, event):
        newlySelectedObjectIndex = self.find_child_object(event.x(), event.y())

        if newlySelectedObjectIndex is None:
            self.selected_duration_object_indicies = [] # Empty all the objects
            self.selection_changed.emit(self.trackID, -1)
        else:
            # Select the object
            if (self.selected_duration_object_indicies.__contains__(newlySelectedObjectIndex)):
                # Already contains the object.
                return
            else:
                # If in single selection mode, be sure to deselect any previous selections before selecting a new one.
                if (self.itemSelectionMode is ItemSelectionOptions.SingleSelection):
                    if (len(self.selected_duration_object_indicies) > 0):
                        # Deselect previously selected item
                        prevSelectedItemIndex = self.selected_duration_object_indicies[0]
                        self.selected_duration_object_indicies.remove(prevSelectedItemIndex)
                        self.durationObjects[prevSelectedItemIndex].on_button_released(event)
                        # self.selection_changed.emit(self.trackID, newlySelectedObjectIndex) # TODO: need to update the selection to deselect the old event?
                        

                # Doesn't already contain the object
                self.selected_duration_object_indicies.append(newlySelectedObjectIndex)
                self.durationObjects[newlySelectedObjectIndex].on_button_clicked(event)
                self.update()
                self.selection_changed.emit(self.trackID, newlySelectedObjectIndex)

    def on_button_released(self, event):
        # Check if we want to dismiss the selection when the mouse button is released (requiring the user to hold down the button to see the results)
        self.selected_object_index = self.find_child_object(event.x(), event.y())

        if event.button() == Qt.LeftButton:
            print("Left click")
        elif event.button() == Qt.RightButton:
            print("Right click")
        elif event.button() == Qt.MiddleButton:
            print("Middle click")
            # Create the partition cut:
            was_cut_made = self.create_comment(event.x())
        else:
            print("Unknown click event!")

        if self.selected_object_index is None:
            # if TimelineTrackDrawingWidget_AnnotationComments.shouldDismissSelectionUponMouseButtonRelease:
            #     self.selection_changed.emit(self.trackID, -1) # Deselect

            # No partitions to create
            return
        else:
            create_comment_index = self.selected_object_index
            # if TimelineTrackDrawingWidget_AnnotationComments.shouldDismissSelectionUponMouseButtonRelease:
            #     self.commentObjects[self.selected_object_index].on_button_released(event)
            #     self.selection_changed.emit(self.trackID, self.selected_object_index)
            

            
        self.update()
                
    def keyPressEvent(self, event):
        gey = event.key()
        self.func = (None, None)
        if gey == Qt.Key_M:
            print("Key 'm' pressed!")
        elif gey == Qt.Key_Right:
            print("Right key pressed!, call drawFundBlock()")
            self.func = (self.drawFundBlock, {})
            self.mModified = True
            self.update()
            self.nextRegion()
        elif gey == Qt.Key_5:
            print("#5 pressed, call drawNumber()")
            self.func = (self.drawNumber, {"notePoint": QPoint(100, 100)})
            self.mModified = True
            self.update()

    def on_mouse_moved(self, event):
        self.hovered_object_index = self.find_child_object(event.x(), event.y())
        # print("on_mouse_moved()",event.x(), event.y(), self.hovered_object_index)
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


    # Annotation/Comment Specific functions:
    def create_comment(self, cut_x):
        # Creates a new cut at the specified position.
        cut_duration_offset = self.offset_to_duration(cut_x)
        cut_datetime = self.offset_to_datetime(cut_x)

        self.annotationEditingDialog = TextAnnotationDialog()
        self.annotationEditingDialog.on_commit.connect(self.try_create_comment)
        self.annotationEditingDialog.on_cancel.connect(self.comment_dialog_canceled)
        self.annotationEditingDialog.set_start_date(cut_datetime)
        self.annotationEditingDialog.set_end_date(cut_datetime)
    
        return False

    def try_create_comment(self, start_date, end_date, title, subtitle, body):
        # Tries to create a new comment
        print('try_create_comment')
        if end_date == start_date:
            end_date = None # This is a work-around because "None" value end_dates can't be passed through a PyQt signal

        # Create the database annotation object
        newAnnotationObj = create_TimestampedAnnotation(start_date, end_date, title, subtitle, body, '')
        self.annotationDataObjects.append(newAnnotationObj)
        save_annotation_events_to_database('/Users/pho/repo/PhoPyQtTimelinePlotter/BehavioralBoxDatabase.db', self.annotationDataObjects)
        self.rebuildDrawnObjects()
        self.update()

    def comment_dialog_canceled(self):
        print('comment_Dialog_canceled')

        


