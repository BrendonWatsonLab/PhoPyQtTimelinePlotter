import sys
from datetime import datetime, timedelta, timezone
from enum import Enum

import numpy as np
from app.database.DatabaseConnectionRef import (
    DatabaseConnectionRef,
    DatabasePendingItemsState,
)
from app.database.entry_models.Behaviors import Behavior, BehaviorGroup, CategoryColors
from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import (
    QDir,
    QEvent,
    QObject,
    QPoint,
    QRect,
    QSize,
    Qt,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPen, QStandardItem
from PyQt5.QtWidgets import (
    QApplication,
    QFileSystemModel,
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
    QTreeView,
    QVBoxLayout,
    QWidget,
)

from phopyqttimelineplotter.GUI.UI.AbstractDatabaseAccessingWidgets import (
    AbstractDatabaseAccessingDialog,
)
from phopyqttimelineplotter.GUI.UI.DialogComponents.AbstractDialogMixins import (
    BoxExperCohortAnimalIDsFrame_Mixin,
    DialogObjectIdentifier,
    ObjectSpecificDialogMixin,
)

# When you set a subtype, ensure that its parent is selected as the type
# When you select a type that's incompatible with the current subtype, probably change the subtype to the first of that type

"""
row_id      .id     array_index
1       1           0
2       2           1
3       3           2


The child (subtype) index that's being retrieved from the type's first child row id is wrong with the additional Noneitem. It needs to have 1 added to it.
"""
## TODO: The type/subtype functionality in this class can be replaced by a child DialogComponents_BoxExperCohortAnimalIDs and the appropriate Mixin
class PartitionEditDialog(
    ObjectSpecificDialogMixin,
    BoxExperCohortAnimalIDsFrame_Mixin,
    AbstractDatabaseAccessingDialog,
):

    # This defines a signal called 'closed' that takes no arguments.
    on_cancel = pyqtSignal(DialogObjectIdentifier)

    # This defines a signal called 'closed' that takes no arguments.
    on_commit = pyqtSignal(
        DialogObjectIdentifier, datetime, datetime, str, str, str, int, int
    )

    def __init__(self, database_connection, parent=None):
        super(PartitionEditDialog, self).__init__(
            database_connection, parent
        )  # Call the inherited classes __init__ method
        self.ui = uic.loadUi(
            "GUI/UI/PartitionEditDialog/PartitionEditDialog.ui", self
        )  # Load the .ui file
        self.enable_none_selection = True  # if true, an "empty" item is added to the combobox dropdown lists which is selected by default
        self.reloadModelFromDatabase()
        self.initUI()
        self.rebuild_combo_boxes_from_behaviors()
        self.show()  # Show the GUI

    def initUI(self):
        self.ui.comboBox_Type.activated[str].connect(self.on_type_combobox_changed)
        self.ui.comboBox_Subtype.activated[str].connect(
            self.on_subtype_combobox_changed
        )

    ## Data Model Functions:
    # Updates the member variables from the database
    # Note: if there are any pending changes, they will be persisted on this action
    def reloadModelFromDatabase(self):
        # Load the latest behaviors and colors data from the database
        self.behaviorGroups = (
            self.database_connection.load_behavior_groups_from_database()
        )
        self.behaviors = self.database_connection.load_behaviors_from_database()

        # if self.enable_none_selection:
        #     self.behaviorGroups.insert(0, None)
        #     self.behaviors.insert(0, None)

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

        last_index = 0
        for (anIndex, aBehaviorGroup) in enumerate(self.behaviorGroups):
            if aBehaviorGroup is None:
                print("FATAL ERROR!!")
                item = QtGui.QStandardItem("", "None")
                item.setData(None)
                # Empty item
            else:
                item = QtGui.QStandardItem(str(aBehaviorGroup.name))
                item.setData(anIndex)
                item.setForeground(aBehaviorGroup.primaryColor.get_QColor())

            types_model.appendRow(item)
            last_index = anIndex

        subtypes_model = self.ui.comboBox_Subtype.model()
        if enable_none_selection:
            first_item = QtGui.QStandardItem("")
            # first_item.setSelectable(True)
            first_item.setData(last_index)
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
            last_index = anIndex

    # def transform_combobox_index_to_array_index(self, combobox_index):
    #     if self.enable_none_selection:
    #         return combobox_index - 1
    #     else:
    #         return combobox_index

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
            return row_id
        else:
            return row_id - 1

    def combo_index_to_array_index(self, combo_index):
        if self.enable_none_selection:
            if combo_index > 0:
                return combo_index - 1
            else:
                return None
        else:
            return combo_index

    # If we want the subtype to always be compatible with the type, we can change the subtype upon setting the type to an incompatible type
    def on_type_combobox_changed(self, text):
        # types changed
        print("type changed: {0}".format(text))
        i1 = self.combo_index_to_array_index(self.ui.comboBox_Type.currentIndex())
        if i1 is None:
            # Set the child to None
            print("Changing child")
            self.set_subtype(None)
            return
        else:
            new_selected_behavior_group = self.behaviorGroups[i1]
            i2 = self.combo_index_to_array_index(
                self.ui.comboBox_Subtype.currentIndex()
            )
            if i2 is None:
                # Need to select the child to the first compatible behavior for the parent
                print("Changing child")
                self.set_subtype(new_selected_behavior_group.behaviors[0].id)
                return
            else:
                selected_behavior = self.behaviors[i2]
                proper_parent_group = selected_behavior.parentGroup
                if proper_parent_group.id == new_selected_behavior_group.id:
                    # The parent is currently already set as the type
                    pass
                else:
                    # Need to select the child to the first compatible behavior for the parent
                    print("Changing child")
                    self.set_subtype(new_selected_behavior_group.behaviors[0].id)

    def on_subtype_combobox_changed(self, text):
        print("subtype changed: {0}".format(text))
        i1 = self.combo_index_to_array_index(self.ui.comboBox_Subtype.currentIndex())
        if i1 is None:
            self.set_type(None)
        else:
            new_selected_behavior = self.behaviors[i1]
            new_selected_proper_parent_group = new_selected_behavior.parentGroup
            i2 = self.combo_index_to_array_index(self.ui.comboBox_Type.currentIndex())
            if i2 is None:
                print("Changing parent")
                self.set_type(new_selected_proper_parent_group.id)  # CHECK
            else:
                selected_behavior_group = self.behaviorGroups[i2]
                if selected_behavior_group.id == new_selected_proper_parent_group.id:
                    # The parent is currently already set as the type
                    pass
                else:
                    # Need to select the parent
                    print("Changing parent")
                    self.set_type(new_selected_proper_parent_group.id)  # CHECK

    def accept(self):
        print("accept:")
        # Emit the signal.
        final_type, final_subtype = int(self.get_type() or -1), int(
            self.get_subtype() or -1
        )

        self.on_commit.emit(
            self.get_referred_object_identifier(),
            self.get_start_date(),
            self.get_end_date(),
            self.get_title(),
            self.get_subtitle(),
            self.get_body(),
            final_type,
            final_subtype,
        )
        super(PartitionEditDialog, self).accept()

    def reject(self):
        print("reject:")
        self.on_cancel.emit(self.get_referred_object_identifier())
        super(PartitionEditDialog, self).reject()

    # GOOD
    def set_type(self, type_id):
        if type_id is None:
            self.ui.comboBox_Type.setCurrentIndex(0)
        else:
            # transform_to_index = type_id - 1 # To transform from sqlite3 1-based row indexing. The proper way would be searching for the row with a matching ID
            # if self.enable_none_selection:
            #     transform_to_index = transform_to_index + 1 # add one to move beyond the "None" entry, which is the first in the combobox
            self.ui.comboBox_Type.setCurrentIndex(self.row_id_to_combo_index(type_id))

    # GOOD
    def get_type(self):
        arrayIndex = self.combo_index_to_array_index(
            self.ui.comboBox_Type.currentIndex()
        )
        if arrayIndex is None:
            return None
        else:
            return self.behaviorGroups[arrayIndex].id

    # GOOD
    def set_subtype(self, subtype_id):
        if subtype_id is None:
            self.ui.comboBox_Subtype.setCurrentIndex(0)
        else:
            transform_to_index = (
                subtype_id - 1
            )  # To transform from sqlite3 1-based row indexing. The proper way would be searching for the row with a matching ID
            if self.enable_none_selection:
                transform_to_index = (
                    transform_to_index + 1
                )  # add one to move beyond the "None" entry, which is the first in the combobox
            self.ui.comboBox_Subtype.setCurrentIndex(
                self.row_id_to_combo_index(subtype_id)
            )

    # GOOD
    def get_subtype(self):
        arrayIndex = self.combo_index_to_array_index(
            self.ui.comboBox_Subtype.currentIndex()
        )
        if arrayIndex is None:
            return None
        else:
            return self.behaviors[arrayIndex].id

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

    # # static method to create the dialog and return (date, time, accepted)
    # @staticmethod
    # def getPartitionChanges(database_connection, selectedPartitionObject, parent = None):
    #     dialog = PartitionEditDialog(database_connection, parent)
    #     dialog.set_start_date(selectedPartitionObject.startTime)
    #     dialog.set_end_date(selectedPartitionObject.endTime)
    #     dialog.set_type(selectedPartitionObject.type_id)
    #     dialog.set_subtype(selectedPartitionObject.subtype_id)
    #     dialog.set_title(selectedPartitionObject.name)
    #     dialog.set_subtitle(selectedPartitionObject.subtitle)
    #     dialog.set_body(selectedPartitionObject.body)
    #     result = dialog.exec_()
    #     # Get result after processing
    #     return (dialog.get_start_date(), dialog.get_end_date(), dialog.get_title(), dialog.get_subtitle(), dialog.get_body(), dialog.get_type(), dialog.get_subtype(), result == QDialog.Accepted)
