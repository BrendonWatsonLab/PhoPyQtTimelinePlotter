# EventTrackDrawingWidget.py
# Contains EventTrackDrawingWidget which draws several PhoEvent objects as rectangles or lines within a single track.

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QComboBox, QMenu
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

from GUI.Model.Partitions import *
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidgetBase import *

## TODO:
"""
TODO: Add "undo" functionality to creating cuts. Can use the "cutObjects" to find the last created cut, find the partition created at that timestamp, grab its endTime and then delete it, and then set the endTime of the partition just before it.

"""

# Consts of N "Cuts" that separate a block into N+1 "Partitions"
#  
class TimelineTrackDrawingWidget_Partition(TimelineTrackDrawingWidgetBase):
    shouldDismissSelectionUponMouseButtonRelease = True

    def __init__(self, trackID, partitionObjects, cutObjects, totalStartTime, totalEndTime):
        super(TimelineTrackDrawingWidget_Partition, self).__init__(trackID, totalStartTime, totalEndTime)
        
        self.partitionManager = Partitioner(self.totalStartTime, self.totalEndTime, self, 'partitioner', partitionObjects)
        self.partitionObjects = self.partitionManager.partitions
        ## TODO: can reconstruct partitions from cutObjects, but can't recover the specific partition's info.
        self.cutObjects = cutObjects
        
        self.eventRect = np.repeat(QRect(0,0,0,0), len(self.partitionObjects))
        self.instantaneousEventRect = np.repeat(QRect(0,0,0,0), len(cutObjects))
        # Hovered Object
        self.hovered_object_index = None
        self.hovered_object = None
        self.hovered_object_rect = None
        # Selected Object
        self.selected_object_index = None

        

    
    # Ohhh, paint event is only passing the displayed rectangle in the event, so when it's in a scroll view, only the part that's on the screen is being drawn.
    # But if that's true, why isn't it appearing unchanged when we scroll?
    def paintEvent( self, event ):
        qp = QtGui.QPainter()
        qp.begin( self )
        # TODO: minor speedup by re-using the array of QRect objects if the size doesn't change
        self.eventRect = np.repeat(QRect(0,0,0,0), len(self.partitionObjects))
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
        for (index, obj) in enumerate(self.partitionObjects):
            obj.update()
            self.eventRect[index] = obj.paint(qp, self.totalStartTime, self.totalEndTime, self.totalDuration, drawRect)
        # Draw the instantaneous event objects
        for (index, obj) in enumerate(self.cutObjects):
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

    def cut_partition(self, partition_index, cut_x):
        # Creates a new cut at the specified position.
        cut_duration_offset = self.offset_to_duration(cut_x)
        cut_datetime = self.offset_to_datetime(cut_x)

        if self.partitionManager.cut_partition(partition_index, cut_datetime):
                # Cut successful!
                print("Cut successful! Cut at ", partition_index)
                self.cutObjects.append(PhoDurationEvent(cut_datetime))
                # Update partitions:
                self.partitionObjects = self.partitionManager.partitions
                return True
        else:
            return False
        
    def set_active_filter(self, start_datetime, end_datetime):
        # Draw the duration objects
        for (index, obj) in enumerate(self.partitionObjects):
            obj.is_deemphasized = not obj.overlaps_range(start_datetime, end_datetime)
        # Draw the instantaneous event objects
        for (index, obj) in enumerate(self.cutObjects):
            obj.is_deemphasized = not obj.overlaps_range(start_datetime, end_datetime)
        self.update()

    def on_button_clicked(self, event):
        self.selected_object_index = self.find_child_object(event.x(), event.y())

        if self.selected_object_index is None:
            self.selection_changed.emit(self.trackID, -1)
        else:
            self.partitionObjects[self.selected_object_index].on_button_clicked(event)
            self.update()
            self.selection_changed.emit(self.trackID, self.selected_object_index)

    def on_button_released(self, event):
        # Check if we want to dismiss the selection when the mouse button is released (requiring the user to hold down the button to see the results)
        self.selected_object_index = self.find_child_object(event.x(), event.y())

        if self.selected_object_index is None:
            if TimelineTrackDrawingWidget_Partition.shouldDismissSelectionUponMouseButtonRelease:
                self.selection_changed.emit(self.trackID, -1) # Deselect

            # No partitions to create
            return
        else:
            cut_partition_index = self.selected_object_index
            if TimelineTrackDrawingWidget_Partition.shouldDismissSelectionUponMouseButtonRelease:
                self.partitionObjects[self.selected_object_index].on_button_released(event)
                self.selection_changed.emit(self.trackID, self.selected_object_index)
            
            if event.button() == Qt.LeftButton:
                print("Left click")
            elif event.button() == Qt.RightButton:
                print("Right click")
            elif event.button() == Qt.MiddleButton:
                print("Middle click")
                # Create the partition cut:
                was_cut_made = self.cut_partition(cut_partition_index, event.x())
                if(was_cut_made):
                    self.update()
                    # self.update()
            else:
                print("Unknown click event!")
            
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
        if self.hovered_object_index is None:
            # No object hovered
            QToolTip.hideText()
            self.hovered_object = None
            self.hovered_object_rect = None
            self.hover_changed.emit(self.trackID, -1)
        else:
            self.hovered_object = self.partitionObjects[self.hovered_object_index]
            self.hovered_object_rect = self.eventRect[self.hovered_object_index]
            text = "event: {0}\nstart_time: {1}\nend_time: {2}\nduration: {3}".format(self.hovered_object.name, self.hovered_object.startTime, self.hovered_object.endTime, self.hovered_object.computeDuration())
            QToolTip.showText(event.globalPos(), text, self, self.hovered_object_rect)
            self.hover_changed.emit(self.trackID, self.hovered_object_index)

    def resizeEvent(self, event):
            # self.widget.move(self.width() - self.widget.width() - 2, 2)
            super(TimelineTrackDrawingWidget_Partition, self).resizeEvent(event)
