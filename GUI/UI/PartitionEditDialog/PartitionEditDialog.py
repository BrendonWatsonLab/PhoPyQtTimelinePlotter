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

class PartitionEditDialog(AbstractDatabaseAccessingDialog):

     # This defines a signal called 'closed' that takes no arguments.
    on_cancel = pyqtSignal()

     # This defines a signal called 'closed' that takes no arguments.
    on_commit = pyqtSignal(datetime, datetime, str, str, str, int, int)


    def __init__(self, database_connection, parent=None):
        super(PartitionEditDialog, self).__init__(database_connection, parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/PartitionEditDialog/PartitionEditDialog.ui", self) # Load the .ui file
        # self.behaviorsManager = BehaviorsManager()
        # self.init_from_behaviors_manager()
        self.reloadModelFromDatabase()
        self.initUI()
        self.rebuild_combo_boxes_from_behaviors()
        self.show() # Show the GUI

    def initUI(self):
        self.ui.buttonBox.accepted.connect(self.accept)
        self.ui.buttonBox.rejected.connect(self.reject)
        self.ui.comboBox_Type.activated[str].connect(self.on_type_combobox_changed)
        self.ui.comboBox_Subtype.activated[str].connect(self.on_subtype_combobox_changed)


## Data Model Functions:
    # Updates the member variables from the database
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        # Load the latest behaviors and colors data from the database
        self.behaviorGroups = self.database_connection.load_behavior_groups_from_database()
        self.behaviors = self.database_connection.load_behaviors_from_database()


    # def init_from_behaviors_manager(self):
    #     uniqueBehaviorsList = self.behaviorsManager.get_unique_behaviors()
    #     uniqueColorsDict = self.behaviorsManager.color_dictionary
    #     uniqueBehaviorGroupsList = self.behaviorsManager.get_unique_behavior_groups()
    #     uniqueColorGroupsDict = self.behaviorsManager.groups_color_dictionary

    #     self.behaviorInfoOptions = []
    #     self.behaviorInfoGroupsOptions = []
    #     # Behaviors:
    #     for (anIndex, aBehavior) in enumerate(uniqueBehaviorsList):
    #         newObj = BehaviorInfoOptions(aBehavior, aBehavior, anIndex, 0, uniqueColorsDict[aBehavior])
    #         self.behaviorInfoOptions.append(newObj)
    #     # Behavior Groups:
    #     for (anIndex, aBehaviorGroup) in enumerate(uniqueBehaviorGroupsList):
    #         newGroupObj = BehaviorInfoOptions(aBehaviorGroup, aBehaviorGroup, anIndex, 0, uniqueColorGroupsDict[aBehaviorGroup])
    #         self.behaviorInfoGroupsOptions.append(newGroupObj)

    # rebuild_combo_boxes_from_behaviors(): rebuilds the two combo boxes from the behaviors
    def rebuild_combo_boxes_from_behaviors(self):
        types_model = self.ui.comboBox_Type.model()
        for (anIndex, aBehaviorGroup) in enumerate(self.behaviorGroups):
            # self.ui.comboBox_Type.addItem(aBehaviorGroup.name)
            item = QtGui.QStandardItem(str(aBehaviorGroup.name))
            item.setForeground(aBehaviorGroup.primaryColor.get_QColor())
            types_model.appendRow(item)
            # self.ui.comboBox_Type.addItem(item)
            # self.ui.comboBox_Type.setItemData()

        subtypes_model = self.ui.comboBox_Subtype.model()
        for (anIndex, aBehavior) in enumerate(self.behaviors):
            item = QtGui.QStandardItem(str(aBehavior.name))
            item.setForeground(aBehavior.primaryColor.get_QColor())
            subtypes_model.appendRow(item)

            # self.ui.comboBox_Subtype.addItem(aBehavior.name)

        

    def on_type_combobox_changed(self, text):
        # types changed
        print('type changed: {0}'.format(text))
        #TODO: update avaialable subtypes
        # transform_to_type = type_id - 1 # To transform from sqlite3 1-based row indexing. The proper way would be searching for the row with a matching ID
        # self.get_type()
        new_selected_behavior_group = self.behaviorGroups[self.ui.comboBox_Type.currentIndex()]

        # If we want the subtype to always be compatible with the type, we can change the subtype upon setting the type to an incompatible type

        # for (aSubtypeID, aUniqueLeafBehavior) in enumerate(new_selected_behavior_group.behaviors):
        #     if aUniqueLeafBehavior.description:
        #         extra_string = aUniqueLeafBehavior.description
        #     else:
        #         # Otherwise it's the parents' name
        #         extra_string = aUniqueBehaviorGroup.name

        #     aNewNode = QTreeWidgetItem([aUniqueLeafBehavior.name, "(type: {0}, subtype: {1})".format(str(aTypeId), str(aSubtypeID)), extra_string])
        #     aNodeColor = aUniqueLeafBehavior.primaryColor.get_QColor()
        #     aNewNode.setBackground(0, aNodeColor)
        #     aNewGroupNode.addChild(aNewNode)

    def on_subtype_combobox_changed(self, text):
        print('subtype changed: {0}'.format(text))
        new_selected_behavior = self.behaviors[self.ui.comboBox_Subtype.currentIndex()]
        new_selected_proper_parent_group = new_selected_behavior.parentGroup
        selected_behavior_group = self.behaviorGroups[self.ui.comboBox_Type.currentIndex()]
        if (selected_behavior_group.id == new_selected_proper_parent_group.id):
            # The parent is currently already set as the type
            pass
        else:
            # Need to select the parent
            print("Changing parent")
            self.set_type(new_selected_proper_parent_group.id)


        


    def accept(self):
        print('accept:')
        # Emit the signal.
        self.on_commit.emit(self.get_start_date(), self.get_end_date(), self.get_title(), self.get_subtitle(), self.get_body(),
            self.get_type(), self.get_subtype())
        super(PartitionEditDialog, self).accept()

    def reject(self):
        print('reject:')
        self.on_cancel.emit()
        super(PartitionEditDialog, self).reject()

    def set_type(self, type_id):
        transform_to_index = type_id - 1 # To transform from sqlite3 1-based row indexing. The proper way would be searching for the row with a matching ID
        self.ui.comboBox_Type.setCurrentIndex(transform_to_index)
    
    def get_type(self):
        # return self.ui.comboBox_Type.currentIndex()
        return self.behaviorGroups[self.ui.comboBox_Type.currentIndex()].id

    def set_subtype(self, subtype_id):
        transform_to_index = subtype_id - 1 # To transform from sqlite3 1-based row indexing. The proper way would be searching for the row with a matching ID
        self.ui.comboBox_Subtype.setCurrentIndex(transform_to_index)
    
    def get_subtype(self):
        # return self.ui.comboBox_Subtype.currentIndex()
        return self.behaviors[self.ui.comboBox_Subtype.currentIndex()].id

    def set_start_date(self, startDate):
        self.ui.dateTimeEdit_Start.setDateTime(startDate)

    def set_end_date(self, endDate):
        self.ui.dateTimeEdit_End.setDateTime(endDate)

    def get_start_date(self):
        return self.ui.dateTimeEdit_Start.dateTime().toPyDateTime()

    def get_end_date(self):
        return self.ui.dateTimeEdit_End.dateTime().toPyDateTime()

    def get_dates(self):
        return (self.get_start_date(), self.get_end_date())

    def get_title(self):
        return self.ui.lineEdit_Title.text()
    
    def get_subtitle(self):
        return self.ui.lineEdit_Subtitle.text()

    def get_body(self):
        return self.ui.textBrowser_Body.toPlainText()

    def set_title(self, updatedStr):
        self.ui.lineEdit_Title.setText(updatedStr)

    def set_subtitle(self, updatedStr):
        return self.ui.lineEdit_Subtitle.setText(updatedStr)

    def set_body(self, updatedStr):
        return self.ui.textBrowser_Body.setPlainText(updatedStr)
    
