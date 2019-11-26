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
# from app.database.DatabaseConnectionRef import DatabasePendingItemsState, DatabaseConnectionRef
# from app.database.entry_models.Behaviors import Behavior, BehaviorGroup, CategoryColors

# from GUI.UI.DialogComponents.DialogComponents_TypeSubtype import DialogComponents_TypeSubtype

class DialogComponents_TypeSubtype(QFrame):

    def __init__(self, parent=None):
        super(DialogComponents_TypeSubtype, self).__init__(parent=parent) # Call the inherited classes __init__ method
        self.ui = uic.loadUi("GUI/UI/DialogComponents/TypeSubtype_DialogComponents.ui", self) # Load the .ui file
        self.enable_none_selection = True # if true, an "empty" item is added to the combobox dropdown lists which is selected by default
        self.behaviorGroups = []
        self.behaviors = []
        self.initUI()
        # self.rebuild_combo_boxes_from_behaviors()
        self.show() # Show the GUI

    def initUI(self):
        self.ui.comboBox_Type.setEnabled(False)
        self.ui.comboBox_Type.activated[str].connect(self.on_type_combobox_changed)
        self.ui.comboBox_Subtype.setEnabled(False)
        self.ui.comboBox_Subtype.activated[str].connect(self.on_subtype_combobox_changed)
        pass

    def setModel(self, behaviorGroups, behaviors, parent):
        self.setParent(parent)
        self.behaviorGroups = behaviorGroups
        self.behaviors = behaviors
        self.on_update_model()

    def on_update_model(self):
        self.rebuild_combo_boxes_from_behaviors()
        self.update()

    # rebuild_combo_boxes_from_behaviors(): rebuilds the two combo boxes from the behaviors
    def rebuild_combo_boxes_from_behaviors(self):
        enable_none_selection = True

        types_model = self.ui.comboBox_Type.model()
        if enable_none_selection:
            # first_index = types_model.index(0, self.ui.comboBox_Type.modelColumn(), self.ui.comboBox_Type.rootModelIndex())
            first_item = QtGui.QStandardItem("")
            first_item.setData(None)
            # first_item.setSelectable(False)
            types_model.appendRow(first_item)

        for (anIndex, aBehaviorGroup) in enumerate(self.behaviorGroups):
            if aBehaviorGroup is None:
                print("FATAL ERROR!!")
                item = QtGui.QStandardItem("","None")
                item.setData(None)
                # Empty item
            else:
                item = QtGui.QStandardItem(str(aBehaviorGroup.name))
                item.setData(anIndex)
                item.setForeground(aBehaviorGroup.primaryColor.get_QColor())
            
            types_model.appendRow(item)

        subtypes_model = self.ui.comboBox_Subtype.model()
        if enable_none_selection:
            first_item = QtGui.QStandardItem("")
            # first_item.setSelectable(True)
            first_item.setData(anIndex)
            subtypes_model.appendRow(first_item)

        for (anIndex, aBehavior) in enumerate(self.behaviors):
            if aBehavior is None:
                print("FATAL ERROR!!")
                item = QtGui.QStandardItem("")
                item.setData(None)
                # Empty item
            else:
                item = QtGui.QStandardItem(str(aBehavior.name))
                item.setData(anIndex)
                item.setForeground(aBehavior.primaryColor.get_QColor())

            subtypes_model.appendRow(item)


    """ note with set_type(...) and set_subtype(...)
    an input argument of 0 was already invalid (because it's supposed to refer to a 1-indexed ID, not a row index)
        type.id
        1           1
        2           2

        comboIndex, arrayIndex, rowID
        0   0      1
        1   1      2
        2   2      3

        comboIndex, arrayIndex, rowID
        0   None
        1   0      1
        2   1      2
    """

    def row_id_to_combo_index(self, row_id):
        if self.enable_none_selection:
            return (row_id)
        else:
            return (row_id - 1)

    def combo_index_to_array_index(self, combo_index):
        if self.enable_none_selection:
            if (combo_index > 0):
                return (combo_index-1)
            else:
                return None
        else:
            return (combo_index)

    # If we want the subtype to always be compatible with the type, we can change the subtype upon setting the type to an incompatible type
    def on_type_combobox_changed(self, text):
        # types changed
        print('type changed: {0}'.format(text))
        i1 = self.combo_index_to_array_index(self.ui.comboBox_Type.currentIndex())
        if (i1 is None):
            # Set the child to None
            print("Changing child")
            self.set_subtype(None)
            return
        else:
            new_selected_behavior_group = self.behaviorGroups[i1]
            i2 = self.combo_index_to_array_index(self.ui.comboBox_Subtype.currentIndex())
            if (i2 is None):
                # Need to select the child to the first compatible behavior for the parent
                print("Changing child")
                self.set_subtype(new_selected_behavior_group.behaviors[0].id)
                return
            else:
                selected_behavior = self.behaviors[i2]
                proper_parent_group = selected_behavior.parentGroup
                if (proper_parent_group.id == new_selected_behavior_group.id):
                    # The parent is currently already set as the type
                    pass
                else:
                    # Need to select the child to the first compatible behavior for the parent
                    print("Changing child")
                    self.set_subtype(new_selected_behavior_group.behaviors[0].id)

    def on_subtype_combobox_changed(self, text):
        print('subtype changed: {0}'.format(text))
        i1 = self.combo_index_to_array_index(self.ui.comboBox_Subtype.currentIndex())
        if (i1 is None):
            self.set_type(None)
        else:
            new_selected_behavior = self.behaviors[i1]
            new_selected_proper_parent_group = new_selected_behavior.parentGroup
            i2 = self.combo_index_to_array_index(self.ui.comboBox_Type.currentIndex())
            if i2 is None:
                print("Changing parent")
                self.set_type(new_selected_proper_parent_group.id) #CHECK
            else:
                selected_behavior_group = self.behaviorGroups[i2]
                if (selected_behavior_group.id == new_selected_proper_parent_group.id):
                    # The parent is currently already set as the type
                    pass
                else:
                    # Need to select the parent
                    print("Changing parent")
                    self.set_type(new_selected_proper_parent_group.id) #CHECK

    #GOOD
    def set_type(self, type_id):
        if type_id is None:
            self.ui.comboBox_Type.setCurrentIndex(0)
        else:
            # transform_to_index = type_id - 1 # To transform from sqlite3 1-based row indexing. The proper way would be searching for the row with a matching ID
            # if self.enable_none_selection:
            #     transform_to_index = transform_to_index + 1 # add one to move beyond the "None" entry, which is the first in the combobox
            self.ui.comboBox_Type.setCurrentIndex(self.row_id_to_combo_index(type_id))
    
    #GOOD
    def get_type(self):
        arrayIndex = self.combo_index_to_array_index(self.ui.comboBox_Type.currentIndex())
        if (arrayIndex is None):
            return None
        else:
            return self.behaviorGroups[arrayIndex].id

    #GOOD
    def set_subtype(self, subtype_id):
        if subtype_id is None:
            self.ui.comboBox_Subtype.setCurrentIndex(0)
        else:
            transform_to_index = subtype_id - 1 # To transform from sqlite3 1-based row indexing. The proper way would be searching for the row with a matching ID
            if self.enable_none_selection:
                transform_to_index = transform_to_index + 1 # add one to move beyond the "None" entry, which is the first in the combobox
            self.ui.comboBox_Subtype.setCurrentIndex(self.row_id_to_combo_index(subtype_id))
    
    #GOOD
    def get_subtype(self):
        arrayIndex = self.combo_index_to_array_index(self.ui.comboBox_Subtype.currentIndex())
        if (arrayIndex is None):
            return None
        else:
            return self.behaviors[arrayIndex].id
