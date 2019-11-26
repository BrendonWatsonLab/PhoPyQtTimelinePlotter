import sys
from datetime import datetime, timezone, timedelta
import numpy as np
from enum import Enum

from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtWidgets import QMessageBox, QToolTip, QStackedWidget, QHBoxLayout, QVBoxLayout, QSplitter, QFormLayout, QLabel, QFrame, QPushButton, QTableWidget, QTableWidgetItem
from PyQt5.QtWidgets import QApplication, QFileSystemModel, QTreeView, QWidget
from PyQt5.QtGui import QPainter, QBrush, QPen, QColor, QFont, QIcon, QStandardItem
from PyQt5.QtCore import Qt, QPoint, QRect, QObject, QEvent, pyqtSignal, pyqtSlot, QSize, QDir

# from app.BehaviorsList import BehaviorsManager, BehaviorInfoOptions
from app.database.DatabaseConnectionRef import DatabasePendingItemsState, DatabaseConnectionRef
from app.database.entry_models.Behaviors import Behavior, BehaviorGroup, CategoryColors
from GUI.UI.AbstractDatabaseAccessingWidgets import AbstractDatabaseAccessingDialog

# When you set a subtype, ensure that its parent is selected as the type
# When you select a type that's incompatible with the current subtype, probably change the subtype to the first of that type

"""
row_id      .id     array_index
1       1           0
2       2           1
3       3           2


The child (subtype) index that's being retrieved from the type's first child row id is wrong with the additional Noneitem. It needs to have 1 added to it.
"""

class VideoEditDialog(AbstractDatabaseAccessingDialog):

     # This defines a signal called 'closed' that takes no arguments.
    on_cancel = pyqtSignal()

     # This defines a signal called 'closed' that takes no arguments.
    on_commit = pyqtSignal(datetime, datetime, str, str, str, int, int)

    def __init__(self, database_connection, parent=None):
        super(VideoEditDialog, self).__init__(database_connection, parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/VideoEditDialog/VideoEditDialog.ui", self) # Load the .ui file
        self.enable_none_selection = True # if true, an "empty" item is added to the combobox dropdown lists which is selected by default
        self.reloadModelFromDatabase()
        self.initUI()
        self.show() # Show the GUI

    def initUI(self):
        # self.ui.frame_StartEndDates.
        # self.ui.frame_TitleSubtitleBody
        self.ui.frame_TypeSubtype.setModel(self.behaviorGroups, self.behaviors, self)
        return

    ## Data Model Functions:
    # Updates the member variables from the database
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        # Load the latest behaviors and colors data from the database
        self.behaviorGroups = self.database_connection.load_behavior_groups_from_database()
        self.behaviors = self.database_connection.load_behaviors_from_database()
        self.ui.frame_TypeSubtype.setModel(self.behaviorGroups, self.behaviors, self)


    def accept(self):
        print('accept:')
        # Emit the signal.
        final_type, final_subtype = int(self.get_type() or -1), int(self.get_subtype() or -1)
        
        self.on_commit.emit(self.get_start_date(), self.get_end_date(), self.get_title(), self.get_subtitle(), self.get_body(),
            final_type, final_subtype)
        super(VideoEditDialog, self).accept()

    def reject(self):
        print('reject:')
        self.on_cancel.emit()
        super(VideoEditDialog, self).reject()

    
    def set_type(self, type_id):
        self.ui.frame_TypeSubtype.set_type(type_id)
    
    def get_type(self):
        return self.ui.frame_TypeSubtype.get_type()

    def set_subtype(self, subtype_id):
        self.ui.frame_TypeSubtype.set_subtype(subtype_id)
    
    def get_subtype(self):
        return self.ui.frame_TypeSubtype.get_subtype()

    def set_start_date(self, startDate):
        self.ui.frame_StartEndDates.set_start_date(startDate)

    def set_end_date(self, endDate):
        self.ui.frame_StartEndDates.set_end_date(endDate)

    def get_start_date(self):
        return self.ui.frame_StartEndDates.get_start_date()

    def get_end_date(self):
        return self.ui.frame_StartEndDates.get_end_date()

    def get_dates(self):
        return (self.get_start_date(), self.get_end_date())

    def get_title(self):
        return self.ui.frame_TitleSubtitleBody.get_title()
    
    def get_subtitle(self):
        return self.ui.frame_TitleSubtitleBody.get_subtitle()

    def get_body(self):
        return self.ui.frame_TitleSubtitleBody.get_body()

    def set_title(self, updatedStr):
        self.ui.frame_TitleSubtitleBody.set_title(updatedStr)

    def set_subtitle(self, updatedStr):
        self.ui.frame_TitleSubtitleBody.set_subtitle(updatedStr)

    def set_body(self, updatedStr):
        self.ui.frame_TitleSubtitleBody.set_body(updatedStr)
    