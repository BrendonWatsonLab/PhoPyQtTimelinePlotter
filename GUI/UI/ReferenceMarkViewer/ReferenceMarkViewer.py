import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget, QHeaderView
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir


## IMPORTS:
# from GUI.UI.ReferenceMarkViewer.ReferenceMarkViewer import ReferenceMarkViewer, ActiveReferenceMarkersMixin

class ActiveReferenceMarkersMixin(object):
    selection_changed = pyqtSignal(list, list)

    # Must be overriden by user
    def reload_list(self):
        pass

    @pyqtSlot(list)
    def on_active_markers_list_updated(self, newList):
        self.activeMarkersList = newList
        self.activeMetadataList = np.repeat(None, len(self.activeMarkersList)) # Clear the metadata
        self.reload_list()

    @pyqtSlot(list)
    def on_active_markers_metadata_updated(self, newMetadata):
        self.activeMetadataList = newMetadata
        self.reload_list()


class ReferenceMarkViewer(ActiveReferenceMarkersMixin, QWidget):

    # selection_changed = pyqtSignal(list, list)
    action_create_comment = pyqtSignal(datetime, datetime)

    action_align_left = pyqtSignal(datetime)
    action_align_right = pyqtSignal(datetime)

    def __init__(self, activeMarkersList, parent=None):
        super(ReferenceMarkViewer, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/ReferenceMarkViewer/ReferenceMarkViewer.ui", self) # Load the .ui file
        self.activeMarkersList = activeMarkersList
        self.activeMetadataList = np.repeat(None, len(activeMarkersList))
        self.setWindowTitle("Active Reference Marks")

        self.initUI()
        self.reload_list()

        self.show() # Show the GUI


    def initUI(self):

        self.setWindowFlags(Qt.WindowStaysOnTopHint)

        self.ui.tableWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.ui.tableWidget.itemClicked.connect(self.on_item_clicked)
        self.ui.tableWidget.setColumnCount(3)
                # Headers
        self.ui.tableWidget.setItem(0,0,QTableWidgetItem("ID"))
        self.ui.tableWidget.setItem(0,1,QTableWidgetItem("Name"))
        self.ui.tableWidget.setItem(0,2,QTableWidgetItem("Datetime"))

        self.ui.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

        ## Buttons
        self.ui.toolButton_RemoveReferenceMark.clicked.connect(self.handle_remove_reference_button_pressed)
        self.ui.toolButton_CreateReferenceMark.clicked.connect(self.handle_create_reference_button_pressed)

        self.ui.toolButton_CreateAnnotation.clicked.connect(self.handle_create_comment_button_pressed)

        self.ui.toolButton_AlignLeft.clicked.connect(self.handle_align_left_button_pressed)
        self.ui.toolButton_AlignRight.clicked.connect(self.handle_align_right_button_pressed)

        pass

    def reload_list(self):
        self.ui.tableWidget.clearContents()
        self.ui.tableWidget.setRowCount(len(self.activeMarkersList))

        for (anIndex, anItem) in enumerate(self.activeMarkersList):
            curr_string = ""
            curr_item_view = anItem.get_view()
            curr_item_record = anItem.get_record()
            # Create the new table item            
            # aDataRowIndex = anIndex + 1 # Add one to compensate for the header row
            aDataRowIndex = anIndex # Add one to compensate for the header row
            # self.ui.tableWidget.setItem(aDataRowIndex,0,QTableWidgetItem(str(aRowIndex)))
            self.ui.tableWidget.setItem(aDataRowIndex,0,QTableWidgetItem(curr_item_view.identifier))

            curr_string = str(curr_item_view.get_position_tuple_string())
            self.ui.tableWidget.setItem(aDataRowIndex,1,QTableWidgetItem(curr_string))
            curr_string = curr_item_record.time_string
            self.ui.tableWidget.setItem(aDataRowIndex,2,QTableWidgetItem(curr_string))



    def on_item_clicked(self):
        # note selectedItems() returns a list of selected cells, not rows.
        # selected_items = self.get_selected_items()
        # selected_indicies = []
        # for index in range(len(selected_items)):
        #     aSelectedItem = selected_items[index]
        #     currRow = self.ui.tableWidget.row(aSelectedItem)
        #     selected_indicies.append(currRow)

        selected_indicies = self.get_selected_item_indicies()
        print("Selected indicies: {0}".format(str(selected_indicies)))
        # Do internal state updating on selection changed
        self.update_internal_ui_on_selection_change()
        self.selection_changed.emit(self.activeMarkersList, selected_indicies)
        return

    # update_internal_ui_on_selection_change(): updates the button enable and other properties when the user's selection changes
    def update_internal_ui_on_selection_change(self):
        num_selected_items = self.get_num_selected_items()
        self.ui.toolButton_CreateAnnotation.setEnabled(num_selected_items==2) # enabled only if we have exactly two references selected
        self.ui.toolButton_RemoveReferenceMark.setEnabled(num_selected_items>0)
        self.ui.toolButton_AlignLeft.setEnabled(num_selected_items>0)
        self.ui.toolButton_AlignRight.setEnabled(num_selected_items>0)
        self.update()


    def get_selected_items(self):
        return self.ui.tableWidget.selectedItems()

    def get_num_selected_items(self):
        return len(self.get_selected_item_indicies())
        # selected_items = self.get_selected_items()
        # currRow = self.ui.tableWidget.row(aSelectedItem)

        # list_set = set(list1)
        

    def get_selected_item_indicies(self):
        selected_items = self.get_selected_items()
        selected_indicies = []
        for index in range(len(selected_items)):
            aSelectedItem = selected_items[index]
            currRow = self.ui.tableWidget.row(aSelectedItem)
            selected_indicies.append(currRow)
        # get the unique indicies to deal with the duplicates
        return list(set(selected_indicies))


    # BUTTON HANDLERS:

    def handle_create_comment_button_pressed(self):
        print("handle_create_comment_button_pressed()")
        curr_selected_ref_indicies = self.get_selected_item_indicies()

        # Get datetimes
        first_item_index = curr_selected_ref_indicies[0]
        second_item_index = curr_selected_ref_indicies[1]

        # first_item = selected_ref_lines[0]
        # second_item = selected_ref_lines[1]

        # start_time = self.activeMetadataList[first_item_index]
        # end_time = self.activeMetadataList[second_item_index]

        start_time = self.activeMarkersList[first_item_index].get_record().time
        end_time = self.activeMarkersList[second_item_index].get_record().time

        # TODO: assumes they're in the right order!

        # TODO: can call self.parent().on_track_child_create_comment(...)?

        # TODO: can call self.parent().try_create_comment_from_selected_reference_lines(...)?
        
        self.action_create_comment.emit(start_time, end_time)


    def handle_remove_reference_button_pressed(self):
        print("handle_remove_reference_button_pressed()")
        # self.action_create_comment.emit()

    def handle_create_reference_button_pressed(self):
        print("handle_create_reference_button_pressed()")
        # self.action_create_comment.emit()


    def handle_align_left_button_pressed(self):
        print("handle_align_left_button_pressed()")
        self.action_align_left.emit()

    def handle_align_right_button_pressed(self):
        print("handle_align_right_button_pressed()")
        self.action_align_right.emit()



## TODO: Unused/Unimplemented
class ReferenceMarkViewer_DockWidget(QtWidgets.QDockWidget):

    def __init__(self, activeMarkersList, parent=None):
        super(ReferenceMarkViewer_DockWidget, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/ReferenceMarkViewer/DockWidget_ReferenceMarkViewer.ui", self) # Load the .ui file
        self.activeMarkersList = activeMarkersList
        self.activeMetadataList = np.repeat(None, len(activeMarkersList))
        self.setWindowTitle("Active Reference Marks")

        self.initUI()
        self.show() # Show the GUI


    def initUI(self):
        pass

