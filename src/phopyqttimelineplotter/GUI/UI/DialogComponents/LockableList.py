# LockableList.py
# Generated from c:\Users\halechr\repo\PhoPyQtTimelinePlotter\GUI\UI\DialogComponents\LockableList.ui automatically by PhoPyQtClassGenerator VSCode Extension
import sys
from datetime import datetime, timedelta, timezone
from enum import Enum

import numpy as np
from phopyqttimelineplotter.app.database.entry_models.DatabaseBase import Base, metadata
from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import (
    QDir,
    QEvent,
    QItemSelectionModel,
    QObject,
    QPersistentModelIndex,
    QPoint,
    QRect,
    QSize,
    Qt,
    pyqtSignal,
    pyqtSlot,
)
from PyQt5.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPen
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QFileSystemModel,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMenu,
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
from sqlalchemy import Column, ForeignKey, Integer, Table, Text, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import NullType

# create QTable Model/View
from phopyqttimelineplotter.GUI.Model.AlchemicalModels.alchemical_model import (
    SqlAlchemyTableModel,
)
from phopyqttimelineplotter.GUI.UI.AbstractDatabaseAccessingWidgets import (
    AbstractDatabaseAccessingWidget,
)
from phopyqttimelineplotter.GUI.UI.DialogComponents.ListLockableEditButtons_DialogComponents import (
    ListLockableEditButtons_DialogComponents,
)

## IMPORTS:
# from phopyqttimelineplotter.GUI.UI.DialogComponents.LockableList import LockableList


class LockableListMainWidgetType(Enum):
    listWidget = 1
    tableWidget = 2


""" LockableList: a list widget with edit controls at the bottom to enable/disable adding/removing items from the list

lblListTitle: the title of the list

listView: the main list (QListView)
tableView: the main table (QTableView)


listLockableEditWidget: ListLockableEditButtons_DialogComponents

"""
# AbstractDatabaseAccessingWidget
class LockableList(AbstractDatabaseAccessingWidget):

    isEditingChanged = pyqtSignal(bool)
    action_plus_pressed = pyqtSignal()
    action_minus_pressed = pyqtSignal()

    # emitted when the list selection changes. Used to enable/disable the minus button in its listLockableEditWidget and to inform any interested parents
    action_selection_changed = pyqtSignal(int)

    lockableListMainWidgetType = LockableListMainWidgetType.tableWidget

    def __init__(self, parent=None):
        super().__init__(
            None, parent=parent
        )  # Call the inherited classes __init__ method
        self.ui = uic.loadUi(
            "GUI/UI/DialogComponents/LockableList.ui", self
        )  # Load the .ui file

        # Set model and selection model
        self.active_record_class = None
        self.active_record_class_string = ""
        self.active_record_class_column_names = None

        self.model = None
        self.selection_model = None

        self.setMouseTracking(True)
        self.initUI()
        self.show()  # Show the GUI

    def initUI(self):
        if (
            LockableList.lockableListMainWidgetType
            == LockableListMainWidgetType.listWidget
        ):
            self.ui.listView.setVisible(True)
            self.ui.tableView.setVisible(False)
            pass
        elif (
            LockableList.lockableListMainWidgetType
            == LockableListMainWidgetType.tableWidget
        ):
            self.ui.listView.setVisible(False)
            self.ui.tableView.setVisible(True)

            # Setup table
            self.ui.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.ui.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.ui.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
            self.ui.tableView.customContextMenuRequested.connect(
                self.display_context_menu
            )
            self.ui.tableView.setSelectionMode(QAbstractItemView.SingleSelection)

            self.ui.tableView.resizeColumnsToContents()
            pass
        else:
            print("ERROR: INVALID!")
            self.ui.listView.setVisible(False)
            self.ui.tableView.setVisible(False)
            pass

        self.ui.listLockableEditWidget.isLockedChanged.connect(self.handle_lock_toggled)
        self.ui.listLockableEditWidget.action_plus_pressed.connect(
            self.handle_plus_button_pressed
        )
        self.ui.listLockableEditWidget.action_minus_pressed.connect(
            self.handle_minus_button_pressed
        )

        pass

    # def __str__(self):
    # 	return 'tEST'

    # Called to setup the record class
    def set_record_class(
        self, new_record_class, new_record_class_string, included_column_names
    ):
        self.active_record_class = new_record_class
        self.active_record_class_string = new_record_class_string
        self.active_record_class_column_names = included_column_names

        # Clear the old models
        self.model = None
        self.selection_model = None

        # update the title
        self.set_list_label(self.active_record_class_string)

        # update the model
        self.reloadModelFromDatabase()
        # if self.active_record_class is not None:
        # 	if self.database_connection is not None:
        # 		new_model = self.database_connection.get_table_model(self.active_record_class)

        # 	else:
        # 		print('self.database_connection is none!')
        # 		new_model = None
        # 		pass

        # 	self.update_table_model(new_model)

    def reloadModelFromDatabase(self):
        if self.active_record_class is not None:
            if self.database_connection is not None:
                new_model = self.database_connection.get_table_model(
                    self.active_record_class, self.active_record_class_column_names
                )
                self.update_table_model(new_model)

            else:
                print("reloadModelFromDatabase(): self.database_connection is none!")
                new_model = None
                self.update_table_model(new_model)
                pass

        else:
            print("reloadModelFromDatabase(): self.active_record_class is none!")
            new_model = None
            self.update_table_model(new_model)

    # updates the table model upon set_record_class
    def update_table_model(self, new_model):
        self.model = new_model
        self.ui.tableView.setModel(self.model)
        self.ui.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.ui.tableView.setContextMenuPolicy(Qt.CustomContextMenu)
        self.ui.tableView.customContextMenuRequested.connect(self.display_context_menu)
        self.ui.tableView.setSelectionMode(QAbstractItemView.SingleSelection)

        self.selection_model = QItemSelectionModel(self.model)
        self.ui.tableView.setModel(self.selection_model.model())
        self.ui.tableView.setSelectionModel(self.selection_model)
        self.selection_model.selectionChanged.connect(self.update_current_record)

        self.ui.tableView.resizeColumnsToContents()

    # Called to update the title of the list
    def set_list_label(self, titleStr):
        self.ui.lblListTitle.setText(titleStr)

    @pyqtSlot()
    def handle_plus_button_pressed(self):
        print("LockableList.handle_plus_button_pressed()")
        self.action_plus_pressed.emit()
        self.create_new_record()

    @pyqtSlot()
    def handle_minus_button_pressed(self):
        print("LockableList.handle_minus_button_pressed()")
        self.action_minus_pressed.emit()

    @pyqtSlot(bool)
    def handle_lock_toggled(self, is_checked):
        print(
            "LockableList.handle_lock_toggled(is_checked: {})".format(str(is_checked))
        )
        is_locked = not is_checked
        is_editing = not is_locked

        if is_editing:
            self.ui.tableView.setEditTriggers(QAbstractItemView.AllEditTriggers)
        else:
            self.ui.tableView.setEditTriggers(QAbstractItemView.NoEditTriggers)

        self.isEditingChanged.emit(is_editing)

    ## Table Model manager functions:
    def display_context_menu(self, pos):
        index = self.ui.tableView.indexAt(pos)

        self.menu = QMenu()

        # self.edit_action = self.menu.addAction("Edit")
        # self.edit_action.triggered.connect(self.edit_trial)

        self.duplicate_action = self.menu.addAction("Duplicate")
        self.duplicate_action.triggered.connect(self.duplicate_record)
        self.duplicate_action.setEnabled(False)

        self.delete_action = self.menu.addAction("Delete")
        self.delete_action.triggered.connect(self.delete_record)
        self.delete_action.setEnabled(False)

        table_viewport = self.ui.tableView.viewport()
        self.menu.popup(table_viewport.mapToGlobal(pos))

    def delete_record(self):
        ## TODO: unimplemented
        print("UNIMPLEMENTED!!!")
        # selected_row_index = self.table_selection_model.currentIndex().data(Qt.EditRole)
        index_list = []
        for model_index in self.ui.tableView.selectionModel().selectedRows():
            index = QPersistentModelIndex(model_index)
            index_list.append(index)

        num_items_to_remove = len(index_list)
        reply = QMessageBox.question(
            self,
            "Confirm",
            "Really delete the selected {0} records?".format(num_items_to_remove),
            QMessageBox.Yes,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            for index in index_list:
                self.current_record = self.model.record(index.row())
                self.database_connection.session.delete(self.current_record)
                # self.model.removeRow(index.row())

            # self.database_connection.session.commit()
            # self.model.refresh()

    def duplicate_record(self):
        ## TODO: unimplemented
        print("UNIMPLEMENTED!!!")
        index_list = []
        for model_index in self.ui.tableView.selectionModel().selectedRows():
            index = QPersistentModelIndex(model_index)
            index_list.append(index)

        num_items_to_remove = len(index_list)
        selected_row_index = None
        # Get only first item
        if num_items_to_remove > 0:
            print("duplicating!")
            selected_row_index = index_list[0]
            self.current_record = self.model.record(index.row())
            new = self.current_record.duplicate()
            self.database_connection.session.add(new)
            self.database_connection.session.commit()
            self.model.refresh()

        else:
            print("selection empty!")
            return

        print("done.")

    def create_new_record(self):
        dialog = QInputDialog(self)
        dialog.setLabelText("Please enter the name for the new Record.")
        dialog.textValueSelected.connect(self.store_new_record)
        dialog.exec()

    def store_new_record(self, name):
        # rec = BehavioralBox()
        rec = self.active_record_class()
        rec.name = name

        try:
            self.database_connection.save_to_database(
                [rec], self.active_record_class_string
            )

        except IntegrityError as e:
            print("ERROR: Failed to commit changes! Rolling back", e)
            self.database_rollback()
            return
        except Exception as e:
            print("Other exception! Trying to continue", e)
            self.database_rollback()
            return

        print("storing new record")
        self.model.refresh()

    def update_current_record(self, x, y):
        self.current_record = self.selection_model.currentIndex().data(Qt.EditRole)
