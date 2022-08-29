# ListLockableEditButtons_DialogComponents.py
# Generated from c:\Users\halechr\repo\PhoPyQtTimelinePlotter\GUI\UI\DialogComponents\ListLockableEditButtons_DialogComponents.ui automatically by PhoPyQtClassGenerator VSCode Extension
import sys
from datetime import datetime, timedelta, timezone
from enum import Enum

import numpy as np
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
from PyQt5.QtGui import QBrush, QColor, QFont, QIcon, QPainter, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QFileSystemModel,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QHeaderView,
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

## IMPORTS:
# from phopyqttimelineplotter.GUI.UI.DialogComponents.ListLockableEditButtons_DialogComponents import ListLockableEditButtons_DialogComponents

""" ListLockableEditButtons_DialogComponents: a row of buttons that are visible/hidden based on whether the row is locked/unlocked.

btnAdd
btnToggleLocked
btnMinus

When the btnToggledLocked is:
	unchecked: Locked
	checked: Unlocked
"""


class ListLockableEditButtons_DialogComponents(QFrame):

    isLockedChanged = pyqtSignal(bool)
    action_plus_pressed = pyqtSignal()
    action_minus_pressed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent=parent)  # Call the inherited classes __init__ method
        self.ui = uic.loadUi(
            "GUI/UI/DialogComponents/ListLockableEditButtons_DialogComponents.ui", self
        )  # Load the .ui file

        self.initUI()
        self.show()  # Show the GUI

    def initUI(self):
        self.action_buttons_list = [self.btnAdd, self.btnMinus]

        self.btnToggleLocked.toggled.connect(self.handle_lock_toggled)

        for aButton in self.action_buttons_list:
            # Make sure that changing the state of the lock/unlock button hides/unhides the widget
            # self.btnToggleLocked.toggled.connect(aButton.setVisible)
            # Hide the buttons by default
            aButton.setVisible(False)

        self.btnAdd.clicked.connect(self.handle_plus_button_pressed)
        self.btnMinus.clicked.connect(self.handle_minus_button_pressed)
        #
        # setChecked()
        pass

    # Returns true if the user is currently in edit mode (unlocked)
    def get_is_editing_enabled(self):
        return self.btnToggleLocked.isChecked()

    @pyqtSlot()
    def handle_plus_button_pressed(self):
        print("handle_plus_button_pressed()")
        self.action_plus_pressed.emit()

    @pyqtSlot()
    def handle_minus_button_pressed(self):
        print("handle_minus_button_pressed()")
        self.action_minus_pressed.emit()

    @pyqtSlot(bool)
    def handle_lock_toggled(self, is_checked):
        print("handle_lock_toggled(is_checked: {})".format(str(is_checked)))
        is_locked = not is_checked
        self.isLockedChanged.emit(not is_locked)

        # Make the buttons visible if it's unlocked
        is_editing = not is_locked
        for aButton in self.action_buttons_list:
            aButton.setVisible(is_editing)

    # def __str__(self):
    # 	return
