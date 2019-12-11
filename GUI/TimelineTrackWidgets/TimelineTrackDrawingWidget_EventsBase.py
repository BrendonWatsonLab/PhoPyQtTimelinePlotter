# EventTrackDrawingWidget.py
# Contains EventTrackDrawingWidget which draws several PhoEvent objects as rectangles or lines within a single track.

import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget,QTableWidgetItem
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QLinearGradient
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, QSize

from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidgetBase import TimelineTrackDrawingWidgetBase, ItemSelectionOptions
from GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_SelectionBase import TimelineTrackDrawingWidget_SelectionBase

# durationObjects are PhoDurationEvents
class TimelineTrackDrawingWidget_EventsBase(TimelineTrackDrawingWidget_SelectionBase):
    # This defines a signal called 'hover_changed'/'selection_changed' that takes the trackID and the index of the child object that was hovered/selected
    default_shouldDismissSelectionUponMouseButtonRelease = True
    default_itemSelectionMode = ItemSelectionOptions.MultiSelection


    # child_action_comment = pyqtSignal(object, object)
    child_action_comment = pyqtSignal(int, object)
    

    def __init__(self, trackID, durationObjects, instantaneousObjects, totalStartTime, totalEndTime, database_connection, parent=None, wantsKeyboardEvents=True, wantsMouseEvents=True):
        super(TimelineTrackDrawingWidget_EventsBase, self).__init__(trackID, totalStartTime, totalEndTime, durationObjects, database_connection=database_connection, parent=parent, wantsKeyboardEvents=wantsKeyboardEvents, wantsMouseEvents=wantsMouseEvents)
        # self.durationObjects = durationObjects
        self.instantaneousObjects = instantaneousObjects
        # self.eventRect = np.repeat(QRect(0,0,0,0), len(durationObjects))
        self.instantaneousEventRect = np.repeat(QRect(0,0,0,0), len(instantaneousObjects))
        # Selected Object
        self.shouldDismissSelectionUponMouseButtonRelease = TimelineTrackDrawingWidget_EventsBase.default_shouldDismissSelectionUponMouseButtonRelease
        self.itemSelectionMode = TimelineTrackDrawingWidget_EventsBase.default_itemSelectionMode


        # Set up signals to parent:
        self.child_action_comment.connect(self.parent().on_track_child_create_comment)

        # Set up signals
        self.attach_child_duration_object_signals()

    # attach_child_duration_object_signals(): called to attach the signals to the children duration objects
    def attach_child_duration_object_signals(self):
        for aDurationObject in self.durationObjects:
            aDurationObject.on_info.connect(self.on_child_action_info)
            aDurationObject.on_edit.connect(self.on_child_action_modify)
            aDurationObject.on_annotate.connect(self.on_child_action_comment)
            aDurationObject.on_delete.connect(self.on_child_action_delete)
    
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

        # Draw the linear horizontal gradient.
        lgrad = self.get_background_gradient(drawRect.height())

        # lgrad = QLinearGradient(drawRect.topLeft(), drawRect.bottomLeft())
        # lgrad.setColorAt(0.0, Qt.red)
        # lgrad.setColorAt(1.0, Qt.yellow)
        qp.fillRect(drawRect, lgrad)

        # print("is_emphasized(...): {0}".format(self.is_track_emphasized()))

        # Draw the text label if needed
        # if self.trackLabelText is not None:
        #     oldPen = qp.pen()
        #     oldFont = qp.font()

        #     qp.setPen(TimelineTrackDrawingWidget_SelectionBase.default_TrackTitlePen)
        #     qp.setFont(TimelineTrackDrawingWidget_SelectionBase.default_TrackTitleFont)
        #     qp.drawText(drawRect, Qt.AlignLeft, self.trackLabelText)

        #     qp.setPen(oldPen)
        #     qp.setFont(oldFont)

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


    # Find the next event
    def find_next_event(self, following_datetime):
        for (index, obj) in enumerate(self.durationObjects):
            if (obj.startTime > following_datetime):
                return (index, obj)
        return None # If there is no next event, return None


    # Find the previous event
    # def find_previous_event(self, preceeding_datetime):
    #     for (index, obj) in enumerate(self.durationObjects):
    #         if (obj.startTime > following_datetime):
    #             return (index, obj)
    #     return None # If there is no next event, return None


    # TODO: find_overlapping_events(...) doesn't yet work
    def find_overlapping_events(self):
        currOpenEvents = []
        currTime = None
        overlappingEvents = dict()

        for (index, obj) in enumerate(self.durationObjects):
            currTime = obj.startTime

            for anOpenEventIndex, anOpenEvent in currOpenEvents:
                if (anOpenEvent.endTime <= currTime):
                    # the event is now closed. Remove it from the currOpenEvents array
                    currOpenEvents.remove((anOpenEventIndex, anOpenEvent))
                else:
                    # Otherwise the event is still open and we should check and see if it overlaps this event                    
                    if anOpenEventIndex in overlappingEvents.keys():
                        overlappingEvents[anOpenEventIndex] = overlappingEvents[anOpenEventIndex] + 1
                    else:
                        overlappingEvents[anOpenEventIndex] = 1

            # Add the current to the array of open events            
            currOpenEvents.append((index, obj))


        return overlappingEvents # If there is no next event, return None


    def on_button_clicked(self, event):
        super().on_button_clicked(event)

    def on_button_released(self, event):
        super().on_button_released(event)

    def on_key_pressed(self, event):
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
        super().on_mouse_moved(event)
        # Draw the tooltip if we want
        if (not (self.hovered_object_index is None)):
            text = "event: {0}\nstart_time: {1}\nend_time: {2}\nduration: {3}".format(self.hovered_object.name, self.hovered_object.startTime, self.hovered_object.endTime, self.hovered_object.computeDuration())
            QToolTip.showText(event.globalPos(), text, self, self.hovered_object_rect)
            self.update()


    # Menu Event Handlers:
    def on_child_action_info(self, childIndex):
        print("TimelineTrackDrawingWidget_EventsBase.on_child_action_info({0})".format(str(childIndex)))
        pass

    def on_child_action_modify(self, childIndex):
        print("TimelineTrackDrawingWidget_EventsBase.on_child_action_modify{0})".format(str(childIndex)))
        pass

    def on_child_action_comment(self, childIndex):
        print("TimelineTrackDrawingWidget_EventsBase.on_child_action_comment({0})".format(str(childIndex)))
        selected_obj = self.durationObjects[childIndex]
        if (selected_obj is None):
            print("ERROR: selected duration object is None! Can't perform action!")
            return
        else:
            # Call parent
            self.child_action_comment.emit(self.trackID, selected_obj)
            # Spawn new annotation dialog
            # Need to find annotation track with the appropriate filter            

        return

    def on_child_action_delete(self, childIndex):
        print("TimelineTrackDrawingWidget_EventsBase.on_child_action_delete({0})".format(str(childIndex)))
        pass
