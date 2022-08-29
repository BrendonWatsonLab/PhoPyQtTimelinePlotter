# EventTrackDrawingWidget.py
# Contains EventTrackDrawingWidget which draws several PhoEvent objects as rectangles or lines within a single track.

import sys
from datetime import datetime, timedelta, timezone

import numpy as np
from phopyqttimelineplotter.app.database.SqlAlchemyDatabase import (
    convert_TimestampedAnnotation,
    create_TimestampedAnnotation,
    modify_TimestampedAnnotation,
    modify_TimestampedAnnotation_endDate,
    modify_TimestampedAnnotation_startDate,
)
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import QEvent, QObject, QPoint, QRect, QSize, Qt, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPen
from PyQt5.QtWidgets import (
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QToolTip,
    QVBoxLayout,
)

from phopyqttimelineplotter.GUI.Model.Events.PhoDurationEvent_AnnotationComment import *
from phopyqttimelineplotter.GUI.Model.TrackType import (
    TrackConfigDataCacheMixin,
    TrackConfigMixin,
    TrackType,
)
from phopyqttimelineplotter.GUI.TimelineTrackWidgets.TimelineTrackDrawingWidget_SelectionBase import (
    TimelineTrackDrawingWidget_SelectionBase,
)
from phopyqttimelineplotter.GUI.TimelineTrackWidgets.TimelineTrackDrawingWidgetBase import (
    ItemSelectionOptions,
    TimelineTrackDrawingWidgetBase,
)
from phopyqttimelineplotter.GUI.UI.TextAnnotations.TextAnnotationDialog import *


class TimelineTrackDrawingWidget_AnnotationComments(
    TrackConfigDataCacheMixin,
    TrackConfigMixin,
    TimelineTrackDrawingWidget_SelectionBase,
):
    # This defines a signal called 'hover_changed'/'selection_changed' that takes the trackID and the index of the child object that was hovered/selected
    default_shouldDismissSelectionUponMouseButtonRelease = True
    default_itemSelectionMode = ItemSelectionOptions.SingleSelection

    def __init__(
        self,
        trackConfig,
        totalStartTime,
        totalEndTime,
        database_connection,
        parent=None,
        wantsKeyboardEvents=False,
        wantsMouseEvents=True,
    ):
        self.trackConfig = trackConfig
        super(TimelineTrackDrawingWidget_AnnotationComments, self).__init__(
            trackConfig.get_track_id(),
            totalStartTime,
            totalEndTime,
            [],
            database_connection=database_connection,
            parent=parent,
            wantsKeyboardEvents=wantsKeyboardEvents,
            wantsMouseEvents=wantsMouseEvents,
        )
        # self.durationObjects = durationObjects
        self.instantaneousObjects = []
        # self.eventRect = np.repeat(QRect(0,0,0,0), len(durationObjects))
        self.instantaneousEventRect = np.repeat(
            QRect(0, 0, 0, 0), len(self.instantaneousObjects)
        )

        # Hovered Object
        self.hovered_object_index = None
        self.hovered_object = None
        self.hovered_object_rect = None
        self.hovered_duration_object_indicies = []

        # Selected Object
        self.selected_duration_object_indicies = []
        self.shouldDismissSelectionUponMouseButtonRelease = (
            TimelineTrackDrawingWidget_AnnotationComments.default_shouldDismissSelectionUponMouseButtonRelease
        )
        self.itemSelectionMode = (
            TimelineTrackDrawingWidget_AnnotationComments.default_itemSelectionMode
        )
        self.itemHoverMode = (
            TimelineTrackDrawingWidget_SelectionBase.default_itemHoverMode
        )

        self.setMouseTracking(True)

        self.annotationEditingDialog = None

        self.trackConfig.cacheUpdated.connect(self.on_reloadModelFromConfigCache)

        self.reloadModelFromDatabase()

    ## Data Model Functions:
    # Updates the member variables from the database
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        # Load the latest behaviors and colors data from the database
        # tempAllAnnotationDataObjects = self.database_connection.load_annotation_events_from_database()
        # self.durationRecords = self.trackConfig.filter_records(self.database_connection.get_session())
        # Clear previous stuff before switching
        self.reset_on_reload()

        ## TODO: add it to config cache instead
        self.contexts = self.database_connection.load_contexts_from_database()
        self.performReloadConfigCache()
        self.update()

    # on_reloadModelFromConfigCache(...): called when the config cache updates to reload the widget
    @pyqtSlot()
    def on_reloadModelFromConfigCache(self):
        # print("TimelineTrackDrawingWidget_AnnotationComments.reloadModelFromConfigCache()")
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
            # newAnnotation.on_edit.connect(self.on_annotation_modify_event)
            # newAnnotation.on_edit_by_dragging_handle_start.connect(self.handleStartSliderValueChange)
            # newAnnotation.on_edit_by_dragging_handle_end.connect(self.handleEndSliderValueChange)
            self.durationObjects.append(newAnnotationView)

        self.update()

    # overrides
    def reset_hovered(self):
        super().reset_hovered()

    def reset_selected(self):
        super().reset_selected()

    # Rebuilds the GUI event objects (self.durationObjects) from the self.durationRecords
    # def rebuildDrawnObjects(self):
    #     self.durationObjects = []
    #     for (anIndex, aDataObj) in enumerate(self.durationRecords):
    #         # Create the graphical annotation object
    #         newAnnotation = convert_TimestampedAnnotation(aDataObj, self)
    #         newAnnotation.on_edit.connect(self.on_annotation_modify_event)
    #         newAnnotation.on_edit_by_dragging_handle_start.connect(self.handleStartSliderValueChange)
    #         newAnnotation.on_edit_by_dragging_handle_end.connect(self.handleEndSliderValueChange)
    #         # newAnnotation.on_edit_by_dragging_handle.connect(self.try_resize_comment_with_handles)
    #         # newAnnotation = PhoDurationEvent_AnnotationComment(start_date, end_date, body, title, subtitle)
    #         newAnnotationIndex = len(self.durationObjects)
    #         newAnnotation.setAccessibleName(str(newAnnotationIndex))

    #         self.durationObjects.append(newAnnotation)

    # Returns the currently selected annotation index or None if none are selected
    def get_selected_annotation_index(self):
        return self.get_selected_event_index()

    # Returns the currently selected annotation object or None if none are selected
    def get_selected_annotation(self):
        return self.get_selected_duration_obj()

    def paintEvent(self, event):
        qp = QtGui.QPainter()
        qp.begin(self)
        # TODO: minor speedup by re-using the array of QRect objects if the size doesn't change
        self.eventRect = np.repeat(QRect(0, 0, 0, 0), len(self.durationObjects))
        self.instantaneousEventRect = np.repeat(
            QRect(0, 0, 0, 0), len(self.instantaneousObjects)
        )

        ## TODO: Use viewport information to only draw the currently displayed rectangles instead of having to draw it all at once.
        drawRect = self.rect()

        # Draw the duration objects
        for (index, obj) in enumerate(self.durationObjects):
            self.eventRect[index] = obj.paint(
                qp, self.totalStartTime, self.totalEndTime, self.totalDuration, drawRect
            )

        # Draw the instantaneous event objects
        for (index, obj) in enumerate(self.instantaneousObjects):
            self.instantaneousEventRect[index] = obj.paint(
                qp, self.totalStartTime, self.totalEndTime, self.totalDuration, drawRect
            )

        qp.end()

    def set_active_filter(self, start_datetime, end_datetime):
        # Draw the duration objects
        for (index, obj) in enumerate(self.durationObjects):
            obj.is_deemphasized = not obj.overlaps_range(start_datetime, end_datetime)
        # Draw the instantaneous event objects
        for (index, obj) in enumerate(self.instantaneousObjects):
            obj.is_deemphasized = not obj.overlaps_range(start_datetime, end_datetime)
        self.update()

    def mouseDoubleClickEvent(self, event):
        print("Mouse double clicked! ({0},{1})".format(event.x(), event.y()))

        newlySelectedObjectIndex = self.find_child_object(event.x(), event.y())

        if newlySelectedObjectIndex is None:
            print("Creating new annotation....")
            was_annotation_made = self.create_comment(event.x())
        else:
            # Select the object
            didSelectionChange = self.select(newlySelectedObjectIndex)
            if didSelectionChange:
                # Doesn't already contain the object
                self.durationObjects[newlySelectedObjectIndex].on_button_clicked(event)
                self.update()
                self.selection_changed.emit(self.trackID, newlySelectedObjectIndex)

            # Called once the selected annotation object has been set
            self.on_annotation_modify_event(newlySelectedObjectIndex)

        pass

    def on_button_clicked(self, event):
        super().on_button_clicked(event)

    def on_button_released(self, event):
        # Check if we want to dismiss the selection when the mouse button is released (requiring the user to hold down the button to see the results)
        self.selected_object_index = self.find_child_object(event.x(), event.y())

        if event.button() == Qt.LeftButton:
            print("commentTrack: Left click")

        elif event.button() == Qt.RightButton:
            print("commentTrack: Right click")
            prevHoveredObj = self.hovered_object
            if prevHoveredObj:
                prevHoveredObj.on_button_released(event)
            else:
                print("commentTrack: No valid hoverred object")

            prevSelectedAnnotationObj = self.get_selected_annotation()
            if prevSelectedAnnotationObj:
                print(
                    "commentTrack: Calling child prevSelectedAnnotationObj.on_button_released(event)..."
                )
                # prevSelectedAnnotationObj.on_button_released(event)
            else:
                print("commentTrack: No valid selection object")

        elif event.button() == Qt.MiddleButton:
            print("commentTrack: Middle click")
            # Create the annotation cut:
            was_cut_made = self.create_comment(event.x())
        else:
            print("commentTrack: Unknown click event!")

        if self.selected_object_index is None:
            # if TimelineTrackDrawingWidget_AnnotationComments.shouldDismissSelectionUponMouseButtonRelease:
            #     self.selection_changed.emit(self.trackID, -1) # Deselect

            # No annotations to create
            return
        else:
            create_comment_index = self.selected_object_index
            # if TimelineTrackDrawingWidget_AnnotationComments.shouldDismissSelectionUponMouseButtonRelease:
            #     self.commentObjects[self.selected_object_index].on_button_released(event)
            #     self.selection_changed.emit(self.trackID, self.selected_object_index)

        self.update()

    def on_key_pressed(self, event):
        gey = event.key()
        self.func = (None, None)
        if gey == Qt.Key_M:
            print("commentTrack: Key 'm' pressed!")
        elif gey == Qt.Key_Right:
            print("commentTrack: Right key pressed!, call drawFundBlock()")
            self.func = (self.drawFundBlock, {})
            self.mModified = True
            self.update()
            self.nextRegion()
        elif gey == Qt.Key_5:
            print("commentTrack: #5 pressed, call drawNumber()")
            self.func = (self.drawNumber, {"notePoint": QPoint(100, 100)})
            self.mModified = True
            self.update()

    def on_key_released(self, event):
        pass

    def on_mouse_moved(self, event):
        super().on_mouse_moved(event)
        # if self.hovered_object is None:
        #     return
        # else:
        #     # Pass through event
        #     self.hovered_object.mouseMoveEvent(event)
        #     return

        # self.update()

    # Annotation/Comment Specific functions:
    def create_comment(self, cut_x):
        cut_duration_offset = self.offset_to_duration(cut_x)
        cut_datetime = self.offset_to_datetime(cut_x)
        return self.create_comment_datetime(cut_datetime, cut_datetime)

    def create_comment_datetime(self, start_datetime, end_datetime):
        # TODO: should get the behavioral_box_id, experiment_id, cohort_id, animal_id from the track's context or config or w/e
        self.annotationEditingDialog = TextAnnotationDialog()
        self.annotationEditingDialog.set_referred_object_identifiers(
            self.get_trackID(), None
        )
        self.annotationEditingDialog.on_commit[
            DialogObjectIdentifier, datetime, str, str, str, int, int, int, int
        ].connect(self.try_create_instantaneous_comment)
        self.annotationEditingDialog.on_commit[
            DialogObjectIdentifier,
            datetime,
            datetime,
            str,
            str,
            str,
            int,
            int,
            int,
            int,
        ].connect(self.try_create_comment)
        self.annotationEditingDialog.on_cancel.connect(self.comment_dialog_canceled)
        self.annotationEditingDialog.set_start_date(start_datetime)
        self.annotationEditingDialog.set_end_date(end_datetime)

        ## SHOULD BE SET TO TRACK's global values for these variables.
        ## TODO: the track can have multiple values
        sel_behavioral_box_id, sel_experiment_id, sel_cohort_id, sel_animal_id = (
            None,
            None,
            None,
            None,
        )
        (
            sel_behavioral_box_ids,
            sel_experiment_ids,
            sel_cohort_ids,
            sel_animal_ids,
        ) = self.trackConfig.get_filter().get_ids()
        if sel_behavioral_box_ids is not None:
            sel_behavioral_box_id = sel_behavioral_box_ids[0]
        if sel_experiment_ids is not None:
            sel_experiment_id = sel_experiment_ids[0]
        if sel_cohort_ids is not None:
            sel_cohort_id = sel_cohort_ids[0]
        if sel_animal_ids is not None:
            sel_animal_id = sel_animal_ids[0]
        self.annotationEditingDialog.set_id_values(
            sel_behavioral_box_id, sel_experiment_id, sel_cohort_id, sel_animal_id
        )

        return False

    @pyqtSlot(
        DialogObjectIdentifier, datetime, datetime, str, str, str, int, int, int, int
    )
    def try_create_comment(
        self,
        partition_identifier,
        start_date,
        end_date,
        title,
        subtitle,
        body,
        behavioral_box_id,
        experiment_id,
        cohort_id,
        animal_id,
    ):
        # Tries to create a new comment
        print("try_create_comment")
        if end_date == start_date:
            end_date = None  # This is a work-around because "None" value end_dates can't be passed through a PyQt signal

        # "None-out" the ID's if they're 0
        if behavioral_box_id < 1:
            behavioral_box_id = None
        if experiment_id < 1:
            experiment_id = None
        if cohort_id < 1:
            cohort_id = None
        if animal_id < 1:
            animal_id = None

        # Create the database annotation object
        newAnnotationObj = create_TimestampedAnnotation(
            start_date,
            end_date,
            title,
            subtitle,
            body,
            "",
            behavioral_box_id,
            experiment_id,
            cohort_id,
            animal_id,
        )
        # self.durationRecords.append(newAnnotationObj)
        self.database_connection.save_annotation_events_to_database([newAnnotationObj])
        self.reloadModelFromDatabase()
        self.performReloadConfigCache()

    @pyqtSlot(DialogObjectIdentifier, datetime, str, str, str, int, int, int, int)
    def try_create_instantaneous_comment(
        self,
        partition_identifier,
        start_date,
        title,
        subtitle,
        body,
        behavioral_box_id,
        experiment_id,
        cohort_id,
        animal_id,
    ):
        self.try_create_comment(
            partition_identifier,
            start_date,
            None,
            title,
            subtitle,
            body,
            behavioral_box_id,
            experiment_id,
            cohort_id,
            animal_id,
        )

    # Called by a specific child annotation (double click or menu option) to indicate that it should be edited in a new Annotation Editor Dialog
    @pyqtSlot(int)
    def on_annotation_modify_event(self, childIndex):
        print("on_annotation_modify_event(...)")
        # selectedAnnotationIndex = self.get_selected_annotation_index()
        # selectedAnnotationObject = self.get_selected_annotation()
        selectedAnnotationIndex = childIndex
        selectedAnnotationRecord = self.durationRecords[selectedAnnotationIndex]
        selectedAnnotationView = self.durationObjects[selectedAnnotationIndex]

        if not (selectedAnnotationView is None):
            self.annotationEditingDialog = TextAnnotationDialog()
            self.annotationEditingDialog.set_referred_object_identifiers(
                self.get_trackID(), selectedAnnotationIndex
            )
            self.annotationEditingDialog.on_cancel.connect(self.comment_dialog_canceled)

            self.annotationEditingDialog.set_start_date(
                selectedAnnotationView.startTime
            )
            self.annotationEditingDialog.set_end_date(selectedAnnotationView.endTime)
            # self.annotationEditingDialog.set_type(selectedAnnotationView.type_id)
            # self.annotationEditingDialog.set_subtype(selectedAnnotationView.subtype_id)
            self.annotationEditingDialog.set_title(selectedAnnotationView.title)
            self.annotationEditingDialog.set_subtitle(selectedAnnotationView.subtitle)
            self.annotationEditingDialog.set_body(selectedAnnotationView.name)

            ## SHOULD BE SET TO TRACK's global values for these variables.
            ## TODO: the track can have multiple values
            sel_behavioral_box_id, sel_experiment_id, sel_cohort_id, sel_animal_id = (
                None,
                None,
                None,
                None,
            )
            (
                sel_behavioral_box_ids,
                sel_experiment_ids,
                sel_cohort_ids,
                sel_animal_ids,
            ) = self.trackConfig.get_filter().get_ids()
            if sel_behavioral_box_ids is not None:
                sel_behavioral_box_id = sel_behavioral_box_ids[0]
            if sel_experiment_ids is not None:
                sel_experiment_id = sel_experiment_ids[0]
            if sel_cohort_ids is not None:
                sel_cohort_id = sel_cohort_ids[0]
            if sel_animal_ids is not None:
                sel_animal_id = sel_animal_ids[0]

            self.annotationEditingDialog.set_id_values(
                sel_behavioral_box_id, sel_experiment_id, sel_cohort_id, sel_animal_id
            )

            self.annotationEditingDialog.on_commit[
                DialogObjectIdentifier, datetime, str, str, str, int, int, int, int
            ].connect(self.try_update_instantaneous_comment)
            self.annotationEditingDialog.on_commit[
                DialogObjectIdentifier,
                datetime,
                datetime,
                str,
                str,
                str,
                int,
                int,
                int,
                int,
            ].connect(self.try_update_comment)
        else:
            print("Couldn't get active annotation object to edit!!")

    @pyqtSlot(int)
    def on_annotation_delete_event(self, childIndex):
        print("on_annotation_delete_event(...)")
        selectedAnnotationIndex = childIndex
        selectedAnnotationRecord = self.durationRecords[selectedAnnotationIndex]
        selectedAnnotationView = self.durationObjects[selectedAnnotationIndex]

        if not (selectedAnnotationRecord is None):
            # Delete the record from the database
            self.database_connection.delete_from_database([selectedAnnotationRecord])
            self.database_commit()
            self.reloadModelFromDatabase()

        else:
            print("Couldn't get active annotation object to delete!!")

    # There's a bug in the database design and they're updating but overlapping. Figure this out. A new one is being created each time I change a field. This wasn't happening before.
    @pyqtSlot(
        DialogObjectIdentifier, datetime, datetime, str, str, str, int, int, int, int
    )
    def try_update_comment(
        self,
        partition_identifier,
        start_date,
        end_date,
        title,
        subtitle,
        body,
        behavioral_box_id,
        experiment_id,
        cohort_id,
        animal_id,
    ):
        # Tries to update an existing comment
        print("try_update_comment")
        dialog_child_index = partition_identifier.childID
        # if the referred to child index exists, and is valid within the current array, continue
        if (dialog_child_index is not None) and (
            0 <= dialog_child_index <= (len(self.durationRecords) - 1)
        ):
            currObjToModify = self.durationRecords[dialog_child_index]
            currObjToModify = modify_TimestampedAnnotation(
                currObjToModify,
                start_date,
                end_date,
                title,
                subtitle,
                body,
                "",
                behavioral_box_id,
                experiment_id,
                cohort_id,
                animal_id,
            )
            self.durationRecords[dialog_child_index] = currObjToModify
            self.database_commit()
            self.reloadModelFromDatabase()
        else:
            print(
                "Error: try_update_comment(...): dialog_child_index {0} is not valid".format(
                    str(dialog_child_index)
                )
            )
            # print("Error: unsure what comment to update!")
            return

    @pyqtSlot(DialogObjectIdentifier, datetime, str, str, str, int, int, int, int)
    def try_update_instantaneous_comment(
        self,
        partition_identifier,
        start_date,
        title,
        subtitle,
        body,
        behavioral_box_id,
        experiment_id,
        cohort_id,
        animal_id,
    ):
        self.try_update_comment(
            partition_identifier,
            start_date,
            None,
            title,
            subtitle,
            body,
            behavioral_box_id,
            experiment_id,
            cohort_id,
            animal_id,
        )

    @pyqtSlot(DialogObjectIdentifier)
    def comment_dialog_canceled(self, partition_identifier):
        print("comment_Dialog_canceled")

    ## Resize Time with Handles:

    # @pyqtSlot(datetime, datetime)
    # def try_resize_comment_with_handles(self, start_date, end_date):
    #     # Tries to update an existing comment
    #     print('try_resize_comment_with_handles')

    #     if (not (self.activeEditingAnnotationIndex is None)):
    #         currObjToModify = self.durationRecords[self.activeEditingAnnotationIndex]
    #         currObjToModify = modify_TimestampedAnnotation(currObjToModify, start_date, end_date, currObjToModify.title, currObjToModify.subtitle, currObjToModify.body)
    #         self.durationRecords[self.activeEditingAnnotationIndex] = currObjToModify
    #         self.database_commit()
    #         self.reloadModelFromDatabase()
    #         self.rebuildDrawnObjects()
    #         self.update()
    #     else:
    #         print("Error: unsure what comment to update!")
    #         return

    @pyqtSlot(int, int)
    def handleStartSliderValueChange(self, child_index, value):
        print("handleStartSliderValueChange({0}, {1})".format(str(child_index), value))
        new_datetime = self.offset_to_datetime(value)
        currObjToModify = self.durationRecords[child_index]
        if not (currObjToModify is None):
            print("found object to modify...")
            # currObjToModify = modify_TimestampedAnnotation_startDate(currObjToModify, new_datetime)
            # self.durationRecords[child_index] = currObjToModify
            # self.database_commit()
            # self.reloadModelFromDatabase()
            # self.rebuildDrawnObjects()
            # self.update()
        else:
            print("Error: unsure what comment to update!")
            return

    @pyqtSlot(int, int)
    def handleEndSliderValueChange(self, child_index, value):
        print("handleEndSliderValueChange({0}, {1})".format(str(child_index), value))
        new_datetime = self.offset_to_datetime(value)
        currObjToModify = self.durationRecords[child_index]
        if not (currObjToModify is None):
            print("found object to modify...")
            # currObjToModify = modify_TimestampedAnnotation_endDate(currObjToModify, new_datetime)
            # self.durationRecords[child_index] = currObjToModify
            # self.database_commit()
            # self.reloadModelFromDatabase()
            # self.rebuildDrawnObjects()
            # self.update()
        else:
            print("Error: unsure what comment to update!")
            return
