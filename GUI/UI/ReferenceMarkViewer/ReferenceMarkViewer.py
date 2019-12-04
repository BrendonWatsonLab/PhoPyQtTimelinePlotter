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
            # Create the new table item            
            # aDataRowIndex = anIndex + 1 # Add one to compensate for the header row
            aDataRowIndex = anIndex # Add one to compensate for the header row
            # self.ui.tableWidget.setItem(aDataRowIndex,0,QTableWidgetItem(str(aRowIndex)))
            self.ui.tableWidget.setItem(aDataRowIndex,0,QTableWidgetItem(anItem.identifier))

            if self.activeMetadataList[anIndex] is None:
                curr_string = str(anItem.get_position_tuple_string())
                self.ui.tableWidget.setItem(aDataRowIndex,1,QTableWidgetItem(curr_string))
                self.ui.tableWidget.setItem(aDataRowIndex,2,QTableWidgetItem("No Metadata"))
            else:
                curr_metadata_item = self.activeMetadataList[anIndex]
                # curr_string = ('RefMark[identifier: {0}]: (datetime: {1})'.format(anItem.identifier, str(curr_metadata_item)))
                curr_string = str(curr_metadata_item)
                # curr_string = str(anItem) + str(self.activeMetadataList[anIndex])
                self.ui.tableWidget.setItem(aDataRowIndex,1,QTableWidgetItem(str(anItem.get_position_tuple_string())))
                self.ui.tableWidget.setItem(aDataRowIndex,2,QTableWidgetItem(curr_string))


            # curr_item = QtWidgets.QListWidgetItem(curr_string)

            # # Add it to the table
            # self.ui.tableWidget.insertItem(anIndex, curr_item)


    def on_item_clicked(self):
        selected_items = self.ui.tableWidget.selectedItems()
        selected_indicies = []
        for index in range(len(selected_items)):
            aSelectedItem = selected_items[index]
            currRow = self.ui.tableWidget.row(aSelectedItem)
            selected_indicies.append(currRow)

        print("Selected indicies: {0}".format(str(selected_indicies)))
        self.selection_changed.emit(self.activeMarkersList, selected_indicies)
        return

    def get_selected_items(self):
        return self.ui.tableWidget.selectedItems()
        

    def get_selected_item_indicies(self):
        selected_items = self.get_selected_items()
        selected_indicies = []
        for index in range(len(selected_items)):
            aSelectedItem = selected_items[index]
            currRow = self.ui.tableWidget.row(aSelectedItem)
            selected_indicies.append(currRow)

        return selected_indicies


    # BUTTON HANDLERS:

    def handle_create_comment_button_pressed(self):
        print("handle_create_comment_button_pressed()")
        self.action_create_comment.emit()


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

